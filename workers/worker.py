import os
import json
import redis
import subprocess

REDIS_URL = os.getenv("REDIS_URL")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

print("✅ Worker connected to Redis")

while True:
    _, raw = r.brpop("job_queue")
    job = json.loads(raw)

    job_id = job["job_id"]
    tool = job["tool"]
    args = job["args"]

    r.hset(job_id, mapping={"status": "running", "progress": 30})

    try:
        process = subprocess.Popen(
            ["python", f"tools/multi-tools/{tool}/main.py"] + args.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        out, err = process.communicate()

        r.hset(job_id, mapping={
            "status": "done",
            "progress": 100,
            "output": (out + err).decode()
        })

    except Exception as e:
        r.hset(job_id, mapping={
            "status": "failed",
            "progress": 0,
            "output": str(e)
        })
