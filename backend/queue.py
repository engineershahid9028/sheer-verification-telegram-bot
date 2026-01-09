import os
import json
import uuid
import redis

REDIS_URL = os.getenv("REDIS_URL")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

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


def get_queue_position(job_id):
    jobs = r.lrange("job_queue", 0, -1)
    for i, j in enumerate(jobs):
        data = json.loads(j)
        if data["job_id"] == job_id:
            return len(jobs) - i
    return None
