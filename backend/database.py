import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base, User


engine = create_engine(os.getenv("DATABASE_URL"), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

def get_or_create_user(user_id:int):
    db = SessionLocal()
    u = db.query(User).filter(User.id==user_id).first()
    if not u:
        u = User(id=user_id, credits=1.0)
        db.add(u); db.commit()
    db.close()
    return u
