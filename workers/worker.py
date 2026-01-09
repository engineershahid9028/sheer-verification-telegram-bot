import os
import json
import redis
import subprocess
import time
import signal

# ================= CONFIG =================

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise RuntimeError("❌ REDIS_URL is not set")

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

print("✅ Worker connected to Redis")

# ================= UTILS =================

def update_job(job_id, **fields):
    r.hset(job_id, mapping=fields)


def fail_job(job_id, error):
    update_job(job_id,
        status="failed",
        progress=0,
        output=str(error)
    )


# ================= WORKER LOOP =================

while True:
    try:
        print("⏳ Waiting for job...")
        _, raw = r.brpop("job_queue")
        job = json.loads(raw)

        job_id = job["job_id"]
        tool = job["tool"]
        args = job["args"]

        print(f"▶ Running job {job_id} using {tool}")

        update_job(job_id, status="running", progress=10)

        # ================= RUN TOOL =================

        cmd = ["python", f"tools/multi-tools/{tool}/main.py"] + args.split()

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Progress simulation
        time.sleep(3)
        update_job(job_id, progress=30)

        time.sleep(3)
        update_job(job_id, progress=60)

        try:
            out, err = process.communicate(timeout=600)  # 10 minutes max
        except subprocess.TimeoutExpired:
            process.kill()
            fail_job(job_id, "Execution timeout (10 minutes)")
            continue

        output = (out or "") + (err or "")

        update_job(job_id,
            status="done",
            progress=100,
            output=output
        )

        print(f"✅ Job {job_id} completed")

    except Exception as e:
        print("❌ Worker error:", e)
        time.sleep(5)
