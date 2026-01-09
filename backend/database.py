import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base, User

# Read DATABASE_URL from Railway environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL is not set")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize database tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Get or create user (safe version)
def get_or_create_user(user_id: int):
    db = SessionLocal()

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        user = User(id=user_id, credits=1.0)
        db.add(user)
        db.commit()
        db.refresh(user)

    credits = user.credits
    db.close()

    return {"id": user_id, "credits": credits}
