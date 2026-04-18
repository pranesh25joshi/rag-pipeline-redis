from fastapi import FastAPI, Query, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
from dotenv import load_dotenv
import os
import uuid
import tempfile
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from google import genai
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ragvector.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store to replace Redis queue
jobs = {}

def process_file_background(job_id: str, file_content: bytes, filename: str, collection_name: str = "ragpdf"):
    """
    Process uploaded file content and store embeddings in Qdrant directly via a background task.
    """
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        loader = PyMuPDFLoader(file_path=temp_file_path)
        docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=400
        )
        chunk = text_splitter.split_documents(docs)

        embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001"
        )

        vector_db = QdrantVectorStore.from_documents(
            documents=chunk,
            embedding=embedding_model,
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API"),
            collection_name=collection_name
        )

        print(f"Processed and stored {len(chunk)} chunks from {filename}")
        jobs[job_id] = {
            "status": "finished", 
            "result": {"message": f"Processed successfully.", "collection_name": collection_name}
        }
        
    except Exception as e:
        print(f"Error processing file {filename}: {e}")
        jobs[job_id] = {
            "status": "failed", 
            "result": str(e)
        }
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

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
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return jobs[job_id]
    

@app.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Read file content
    file_content = await file.read()
    filename = file.filename
    
    # Create simple UUID for tracking
    job_id = str(uuid.uuid4())
    
    # Store initial status
    jobs[job_id] = {"status": "in_progress"}
    
    # Process the document as a FastAPI Background Task
    background_tasks.add_task(process_file_background, job_id, file_content, filename)

    return {"status": "queued", "job_id": job_id}