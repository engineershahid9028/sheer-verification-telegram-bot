import os
import redis
from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session

from backend.database import init_db, SessionLocal, get_or_create_user
from backend.models import Tool, Job
from backend.queue import enqueue_job, get_queue_position

# ---------------- CONFIG ----------------

REDIS_URL = os.getenv("REDIS_URL")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# ---------------- APP ----------------

app = FastAPI(title="Sheer Verification Backend")

# ---------------- STARTUP ----------------

@app.on_event("startup")
def startup():
    init_db()
    print("✅ Database initialized")
    print("✅ Redis connected")

# ---------------- HELPERS ----------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- API ----------------

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
    db: Session = SessionLocal()

    # get user
    user = get_or_create_user(user_id)

    # get tool pricing
    tool_obj = db.query(Tool).filter(Tool.name == tool).first()
    if not tool_obj:
        raise HTTPException(404, "Tool not found")

    # check credits
    if user.credits < tool_obj.price:
        raise HTTPException(402, "Not enough credits")

    # deduct credits
    user.credits -= tool_obj.price
    db.commit()

    # enqueue job
    job_id = enqueue_job(user_id, tool, args)
    queue_pos = get_queue_position(job_id)

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
        "queue_position": queue_pos,
        "remaining_credits": user.credits
    }

# ---------------- JOB STATUS ----------------

@app.get("/status/{job_id}")
def job_status(job_id: str):
    data = r.hgetall(job_id)

    if not data:
        return {"job_id": job_id, "status": "queued", "progress": 0}

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

# ---------------- ADMIN: SET TOOL PRICE ----------------

@app.post("/admin/setprice")
def set_price(tool: str, price: float, key: str):
    ADMIN_KEY = os.getenv("ADMIN_KEY", "admin123")

    if key != ADMIN_KEY:
        raise HTTPException(403, "Unauthorized")

    db = SessionLocal()
    tool_obj = db.query(Tool).filter(Tool.name == tool).first()

    if not tool_obj:
        tool_obj = Tool(name=tool, price=price)
        db.add(tool_obj)
    else:
        tool_obj.price = price

    db.commit()
    db.close()

    return {"status": "ok", "tool": tool, "price": price}

# ---------------- ADMIN: GRANT CREDITS ----------------

@app.post("/admin/grant")
def grant_credits(user_id: int, credits: float, key: str):
    ADMIN_KEY = os.getenv("ADMIN_KEY", "admin123")

    if key != ADMIN_KEY:
        raise HTTPException(403, "Unauthorized")

    db = SessionLocal()
    user = get_or_create_user(user_id)
    user.credits += credits
    db.commit()
    db.close()

    return {"status": "ok", "user_id": user_id, "credits_added": credits}

# ---------------- HEALTH ----------------

@app.get("/health")
def health():
    return {
        "backend": "running",
        "redis": r.ping()
    }
