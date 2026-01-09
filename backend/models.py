from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)   # <-- FIXED
    credits = Column(Float, default=1.0)

class Tool(Base):
    __tablename__ = "tools"
    name = Column(String, primary_key=True)
    price = Column(Float, default=1.0)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    user_id = Column(BigInteger)   # <-- also fix here
    tool = Column(String)
    status = Column(String)
    output = Column(String)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(String, primary_key=True)
    user_id = Column(BigInteger)   # <-- also fix here
    method = Column(String)
    amount = Column(Float)
    credits = Column(Float)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
