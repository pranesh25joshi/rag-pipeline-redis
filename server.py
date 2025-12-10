from fastapi import FastAPI, Query ,HTTPException , UploadFile , File

from dotenv  import load_dotenv
from queues.query_processing_worker import query_processing
from queues.file_to_db_worker import file_embedding_and_loading
from client.queue_initialization import queue

load_dotenv()


app= FastAPI()

@app.get("/")
def home():
    return "this is the home route"


@app.post("/chat")
async def chat(
    query : str = Query(..., description="this is the user query for the pdf")):

    job = queue.enqueue(query_processing,query)

    return {"status" : "queued", "job_id" : job.id}

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
    file_location = f"/tmp/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())

    job = queue.enqueue(file_embedding_and_loading, file_location)

    return {"status": "queued", "job_id": job.id}