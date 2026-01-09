import os
import json
import redis
import subprocess
import traceback
import shlex

REDIS_URL = os.getenv("REDIS_URL")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

print("✅ Worker connected to Redis")

TOOLS_ROOT = "tools/multi-tools"

while True:
    _, raw = r.brpop("job_queue")
    job = json.loads(raw)

    job_id = job["job_id"]
    tool = job["tool"]
    args = job["args"]

    print(f"\n▶ JOB {job_id}")
    print(f"▶ TOOL: {tool}")
    print(f"▶ ARGS: {args}")

    r.hset(job_id, mapping={"status": "running", "progress": 30})

    try:
        tool_path = f"{TOOLS_ROOT}/{tool}/main.py"

        if not os.path.exists(tool_path):
            raise Exception(f"Tool not found: {tool_path}")

        cmd = ["python", tool_path] + shlex.split(args)

        print("▶ CMD:", cmd)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        out, err = process.communicate(timeout=180)

        output = ""
        if out:
            output += "\n=== STDOUT ===\n" + out
        if err:
            output += "\n=== STDERR ===\n" + err

        if process.returncode != 0:
            print("❌ TOOL FAILED")
            print(output)

            r.hset(job_id, mapping={
                "status": "failed",
                "progress": 0,
                "output": output or "Tool exited with error"
            })
        else:
            print("✅ TOOL SUCCESS")

            r.hset(job_id, mapping={
                "status": "done",
                "progress": 100,
                "output": output or "Completed successfully"
            })

    except Exception:
        error_text = traceback.format_exc()
        print("🔥 WORKER ERROR")
        print(error_text)

        r.hset(job_id, mapping={
            "status": "failed",
            "progress": 0,
            "output": error_text
        })
