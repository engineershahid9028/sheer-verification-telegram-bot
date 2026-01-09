import os
import redis
from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session

from backend.database import init_db, SessionLocal, get_or_create_user
from backend.models import Tool, Job
from backend.queue import enqueue_job, get_queue_position
from backend.dashboard import router as dashboard_router
app.include_router(dashboard_router)

REDIS_URL = os.getenv("REDIS_URL")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

app = FastAPI(title="Sheer Verification Backend")

# ---------- Startup ----------

@app.on_event("startup")
def startup():
    init_db()
    print("✅ Database initialized")
    print("✅ Redis connected")

# ---------- Root ----------

@app.get("/")
def root():
    return {"status": "ok"}

# ---------- Balance ----------

@app.get("/balance/{user_id}")
def balance(user_id: int):
    user = get_or_create_user(user_id)
    return {"credits": user.credits}

# ---------- Run Tool ----------

@app.post("/run")
def run_tool(user_id: int, tool: str, args: str):
    db: Session = SessionLocal()

    user = get_or_create_user(user_id)

    tool_obj = db.query(Tool).filter(Tool.name == tool).first()
    if not tool_obj:
        raise HTTPException(404, "Tool not found")

    if user.credits < tool_obj.price:
        raise HTTPException(402, "Not enough credits")

    # deduct credits
    user.credits -= tool_obj.price
    db.commit()

    # enqueue job
    job_id = enqueue_job(user_id, tool, args)
    queue_pos = get_queue_position(job_id)

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

# ---------- Job Status ----------

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

# ---------- User Jobs ----------

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

# ---------- Admin: Set Tool Price ----------

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

# ---------- Admin: Grant Credits ----------

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

# ---------- Health ----------

@app.get("/health")
def health():
    return {
        "backend": "running",
        "redis": r.ping()
    }
