from redis import Redis
from rq import Queue
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Simple enqueue helper. The worker will execute the function named 'worker.process'.
# We use the string reference to avoid importing worker module here.

def enqueue_analysis(image_path: str, endereco: str, meta: dict | None = None):
    conn = Redis.from_url(REDIS_URL)
    q = Queue(connection=conn)
    payload = {"image_path": image_path, "endereco": endereco, "meta": meta or {}}
    # enqueue a function called 'process' from the worker module
    q.enqueue("worker.process", payload)
    return True
