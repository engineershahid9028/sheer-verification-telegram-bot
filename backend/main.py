from fastapi import FastAPI, HTTPException
from backend.database import init_db, SessionLocal, get_or_create_user
from backend.models import Tool, Job
from backend.queue import enqueue_job, get_queue_position


app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()

@app.post("/run")
def run(user_id:int, tool:str, args:str):
    db=SessionLocal()
    user = get_or_create_user(user_id)
    t = db.query(Tool).filter(Tool.name==tool).first()
    if not t: raise HTTPException(404,"Tool not found")
    if user.credits < t.price: raise HTTPException(402,"Not enough credits")
    user.credits -= t.price
    job_id = enqueue_job(user_id, tool, args)
    db.add(Job(id=job_id,user_id=user_id,tool=tool,status="queued"))
    db.commit(); db.close()
    return {"job_id":job_id, "queue_position": get_queue_position(job_id), "remaining_credits": user.credits}
