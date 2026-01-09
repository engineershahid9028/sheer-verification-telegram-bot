import os
import json
import uuid
import redis
import time

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise RuntimeError("❌ REDIS_URL not set for queue")

def connect_redis():
    while True:
        try:
            r = redis.Redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_keepalive=True,
                socket_timeout=30
            )
            r.ping()
            print("✅ Queue connected to Redis")
            return r
        except Exception as e:
            print("❌ Redis connection failed, retrying in 5s:", e)
            time.sleep(5)

r = connect_redis()

# ---------------- JOB QUEUE ----------------

def enqueue_job(user_id, tool, args):
    job_id = str(uuid.uuid4())[:8]

    job = {
        "job_id": job_id,
        "user_id": user_id,
        "tool": tool,
        "args": args,
        "status": "queued",
        "progress": 0
    }

    r.lpush("job_queue", json.dumps(job))
    return job_id
