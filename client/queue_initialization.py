from rq import Queue
from redis import Redis
from dotenv import load_dotenv
import os

load_dotenv()

# For Upstash Redis TCP connection
REDIS_HOST = os.getenv("REDIS_HOST", "bursting-piglet-36655.upstash.io")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")  # The password from redis://default:PASSWORD@host:port

redis_client = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    ssl=True,
    decode_responses=False
)

queue = Queue(connection=redis_client)
