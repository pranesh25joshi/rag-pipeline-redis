from rq import Queue
from dotenv import load_dotenv
import os
from upstash_redis import Redis

load_dotenv()

UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")


redis_client= Redis(
    url=UPSTASH_REDIS_URL,
    token=UPSTASH_REDIS_TOKEN
)

queue = Queue(connection=redis_client)