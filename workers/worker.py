import os
import json
import redis
import subprocess
import time

REDIS_URL = os.getenv("REDIS_URL")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

print("✅ Worker connected to Redis")

while True:
    _, raw = r.brpop("job_queue")
    job = json.loads(raw)

    job_id = job["job_id"]
    tool = job["tool"]
    args = job["args"]

    print(f"▶ Running job {job_id} using {tool}")

    r.hset(job_id, mapping={"status": "running", "progress": 20})

    try:
        cmd = ["python", f"tools/multi-tools/{tool}/main.py"] + args.split()

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Give tool up to 5 minutes
        start = time.time()
        timeout = 300

        while True:
            if process.poll() is not None:
                break

            if time.time() - start > timeout:
                process.kill()
                raise Exception("Tool execution timeout (300s)")

            time.sleep(2)

        out, err = process.communicate()

        r.hset(job_id, mapping={
            "status": "done",
            "progress": 100,
            "output": (out + err)
        })

        print(f"✅ Job {job_id} completed")

    except Exception as e:
        print("❌ Worker error:", e)

        r.hset(job_id, mapping={
            "status": "failed",
            "progress": 0,
            "output": str(e)
        })
