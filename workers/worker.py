import os
import json
import redis
import subprocess
import time

REDIS_URL = os.getenv("REDIS_URL")

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
            print("✅ Worker connected to Redis")
            return r
        except Exception as e:
            print("❌ Redis connection failed, retrying in 5s:", e)
            time.sleep(5)

r = connect_redis()

while True:
    try:
        job = r.brpop("job_queue", timeout=30)

        if not job:
            continue  # timeout, loop again

        _, raw = job
        job = json.loads(raw)

        job_id = job["job_id"]
        tool = job["tool"]
        args = job["args"]

        print(f"▶ Running job {job_id} using {tool}")

        r.hset(job_id, mapping={"status": "running", "progress": 30})

        process = subprocess.Popen(
            ["python", f"tools/multi-tools/{tool}/main.py"] + args.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        out, err = process.communicate(timeout=300)

        r.hset(job_id, mapping={
            "status": "done",
            "progress": 100,
            "output": (out + err).decode(errors="ignore")
        })

    except subprocess.TimeoutExpired:
        r.hset(job_id, mapping={
            "status": "failed",
            "progress": 0,
            "output": "Execution timeout"
        })

    except redis.exceptions.ConnectionError:
        print("❌ Redis disconnected. Reconnecting...")
        r = connect_redis()

    except Exception as e:
        print("❌ Worker error:", e)
        time.sleep(2)
