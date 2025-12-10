from rq import Queue
from redis import Redis
from dotenv import load_dotenv
import os

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))

queue = Queue(connection=Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
))