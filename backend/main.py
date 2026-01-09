import os
import redis
from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session

from backend.database import init_db, SessionLocal, get_or_create_user
from backend.models import Tool, Job, User
from backend.queue import enqueue_job

# ---------------- CONFIG ----------------

REDIS_URL = os.getenv("REDIS_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

if not REDIS_URL:
    raise RuntimeError("❌ REDIS_URL is not set")

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL is not set")

try:
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    print("✅ Redis connected")
except Exception as e:
    raise RuntimeError(f"❌ Redis connection failed: {e}")

# ---------------- APP ----------------

app = FastAPI(title="Sheer Verification Backend")

# ---------------- STARTUP ----------------

@app.on_event("startup")
def startup():
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        raise RuntimeError(f"❌ Database init failed: {e}")

# ---------------- ROOT ----------------

@app.get("/")
def root():
    return {"status": "ok"}

# ---------------- BALANCE ----------------

@app.get("/balance/{user_id}")
def balance(user_id: int):
    user = get_or_create_user(user_id)
    return {"credits": user["credits"]}

# ---------------- RUN TOOL ----------------
@app.post("/run")
def run_tool(user_id: int, tool: str, args: str):
    try:
        db = SessionLocal()

        user = get_or_create_user(user_id)

        tool_obj = db.query(Tool).filter(Tool.name == tool).first()
        if not tool_obj:
            raise HTTPException(status_code=404, detail=f"Tool not found: {tool}")

        if user.credits < tool_obj.price:
            raise HTTPException(status_code=402, detail="Not enough credits")

        # deduct credits
        user.credits -= tool_obj.price
        db.commit()

        # enqueue job
        job_id = enqueue_job(user_id, tool, args)

        # save job
        job = Job(
            id=job_id,
            user_id=user_id,
            tool=tool,
            status="queued",
            output=""
        )
        db.add(job)
        db.commit()
        db.close()

        return {
            "job_id": job_id,
            "status": "queued",
            "remaining_credits": user.credits
        }

    except HTTPException:
        raise

    except Exception as e:
        print("❌ RUN ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- JOB STATUS ----------------

@app.get("/status/{job_id}")
def job_status(job_id: str):
    data = r.hgetall(job_id)

    if not data:
        return {
            "job_id": job_id,
            "status": "queued",
            "progress": 0
        }

    return {
        "job_id": job_id,
        "status": data.get("status", "unknown"),
        "progress": int(data.get("progress", 0)),
        "output": data.get("output", "")
    }

# ---------------- USER JOBS ----------------

@app.get("/jobs/{user_id}")
def user_jobs(user_id: int):
    db = SessionLocal()
    jobs = db.query(Job).filter(Job.user_id == user_id).all()

    result = [
        {
            "id": j.id,
            "tool": j.tool,
            "status": j.status
        }
        for j in jobs
    ]

    db.close()
    return result

# ---------------- HEALTH ----------------

@app.get("/health")
def health():
    return {
        "backend": "running",
        "redis": r.ping()
    }
