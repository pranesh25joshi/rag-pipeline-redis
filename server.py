from fastapi import FastAPI, Query, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
from dotenv import load_dotenv
from queues.file_to_db_worker import file_embedding_and_loading
from client.queue_initialization import queue
import os
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from google import genai
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ragvector.vercel.app", 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return "this is the home route"


@app.post("/chat")
async def chat(
    query: str = Query(..., description="this is the user query for the pdf"),
    collection_name: str = Query("ragpdf", description="Qdrant collection name"),
    top_k: int = Query(5, description="Number of similar documents to retrieve")
):
    """
    Direct streaming chat endpoint - No Redis queue for instant responses.
    Uses async/await for IO-bound operations (Gemini + Qdrant).
    """
    try:
        # Get embeddings and search Qdrant
        embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001"
        )
        
        vector_db = QdrantVectorStore.from_existing_collection(
            embedding=embedding_model,
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API"),
            collection_name=collection_name
        )
        
        search_result = await run_in_threadpool(
            vector_db.similarity_search, 
            query=query, 
            k=top_k
        )
        context = "\n\n".join([r.page_content for r in search_result])
        
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        
        def generate_stream():
            response = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=f"Context: {context}\n\nQuery: {query}\n\nProvide a detailed answer based on the context."
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        
        return StreamingResponse(generate_stream(), media_type="text/plain")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.get("/job-status")
async def get_result(
    job_id: str = Query(..., description="Job ID")
):
    try:
        job = queue.fetch_job(job_id=job_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.is_finished:
        return {"status": "finished", "result": job.result}
    elif job.is_failed:
        return {"status": "failed", "result": str(job.exc_info)}
    else:
        return {"status": "in_progress"}
    

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Read file content
    file_content = await file.read()
    filename = file.filename
    
    # Enqueue job with file content and filename
    job = queue.enqueue(file_embedding_and_loading, file_content, filename)

    return {"status": "queued", "job_id": job.id}