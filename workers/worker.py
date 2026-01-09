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
    try:
        _, raw = r.brpop("job_queue")
        job = json.loads(raw)

        job_id = job["job_id"]
        tool = job["tool"]
        args = job["args"]

        print(f"▶ Running job {job_id} with tool {tool}")
        print(f"▶ Args: {args}")

        r.hset(job_id, mapping={
            "status": "running",
            "progress": 30
        })

        tool_path = f"{TOOLS_ROOT}/{tool}/main.py"

        if not os.path.exists(tool_path):
            raise Exception(f"Tool not found: {tool_path}")

        cmd = ["python", tool_path] + shlex.split(args)

        print("▶ Command:", cmd)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            out, err = process.communicate(timeout=180)
        except subprocess.TimeoutExpired:
            process.kill()
            raise Exception("Tool execution timed out (180s)")

        output = ""
        if out:
            output += "\n=== STDOUT ===\n" + out
        if err:
            output += "\n=== STDERR ===\n" + err

        if process.returncode != 0:
            print("❌ Tool failed")
            print(output)

            r.hset(job_id, mapping={
                "status": "failed",
                "progress": 0,
                "output": output or "Tool exited with error"
            })
        else:
            print("✅ Tool finished successfully")

            r.hset(job_id, mapping={
                "status": "done",
                "progress": 100,
                "output": output or "Completed successfully"
            })

    except Exception as e:
        error_text = traceback.format_exc()
        print("🔥 Worker exception:", error_text)

        try:
            r.hset(job_id, mapping={
                "status": "failed",
                "progress": 0,
                "output": error_text
            })
        except:
            pass
