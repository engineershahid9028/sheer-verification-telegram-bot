import os
import redis
from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session

from backend.database import init_db, SessionLocal, get_or_create_user
from backend.models import Tool, Job
from backend.queue import enqueue_job, get_queue_position
from backend.dashboard import router as dashboard_router

# ---------------- CONFIG ----------------

REDIS_URL = os.getenv("REDIS_URL")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# ---------------- APP ----------------

app = FastAPI(title="Sheer Verification Backend")

# include dashboard AFTER app is created
app.include_router(dashboard_router)

# ---------------- STARTUP ----------------

@app.on_event("startup")
def startup():
    init_db()
    print("✅ Database initialized")
    print("✅ Redis connected")

# ---------------- ROOT ----------------

@app.get("/")
def root():
    return {"status": "ok"}

# ---------------- BALANCE ----------------

@app.get("/balance/{user_id}")
def balance(user_id: int):
    user = get_or_create_user(user_id)
    return {"credits": user.credits}

# ---------------- RUN TOOL ----------------
@app.post("/run")
def run_tool(user_id: int, tool: str, args: str):
    db = SessionLocal()

    user = get_or_create_user(user_id)
    tool_obj = db.query(Tool).filter(Tool.name == tool).first()

    if not tool_obj:
        raise HTTPException(404, "Tool not found")

    if user.credits < tool_obj.price:
        raise HTTPException(402, "Not enough credits")

    # deduct credits
    user.credits -= tool_obj.price
    db.commit()

    # enqueue job (do NOT wait for worker)
    job_id = enqueue_job(user_id, tool, args)

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
    db.close()

    return [
        {
            "id": j.id,
            "tool": j.tool,
            "status": j.status
        }
        for j in jobs
    ]

# ---------------- HEALTH ----------------

@app.get("/health")
def health():
    return {
        "backend": "running",
        "redis": r.ping()
    }
