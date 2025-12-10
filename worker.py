"""
Background worker for processing heavy CPU-bound tasks (PDF ingestion).
Run this separately from your FastAPI server.

Usage:
    python worker.py
"""
import os
from dotenv import load_dotenv
from rq import Worker
from client.queue_initialization import queue, redis_client

load_dotenv()

if __name__ == '__main__':
    print("🚀 Starting RQ Worker...")
    print(f"📡 Connected to Redis: {os.getenv('UPSTASH_REDIS_REST_URL')}")
    print("👷 Listening for jobs on the default queue...")
    
    worker = Worker([queue], connection=redis_client)
    worker.work()
