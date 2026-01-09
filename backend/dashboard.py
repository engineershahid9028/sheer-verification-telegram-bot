from fastapi import APIRouter
from backend.database import SessionLocal
from backend.models import User, Job, Payment

router = APIRouter(prefix="/dashboard")

@router.get("/users")
def users():
    db = SessionLocal()
    users = db.query(User).all()
    return [{"id":u.id,"credits":u.credits} for u in users]

@router.get("/jobs")
def jobs():
    db = SessionLocal()
    jobs = db.query(Job).all()
    return [{"id":j.id,"status":j.status} for j in jobs]

@router.get("/payments")
def payments():
    db = SessionLocal()
    pays = db.query(Payment).all()
    return [{"id":p.id,"amount":p.amount,"status":p.status} for p in pays]
