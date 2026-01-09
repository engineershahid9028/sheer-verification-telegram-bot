from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    credits = Column(Float, default=1.0)
    referred_by = Column(Integer, nullable=True)
    last_daily = Column(DateTime, nullable=True)
    subscription = Column(Boolean, default=False)

class Tool(Base):
    __tablename__ = "tools"
    name = Column(String, primary_key=True)
    price = Column(Float, default=1.0)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    user_id = Column(Integer)
    tool = Column(String)
    status = Column(String)
    output = Column(String)

class Promo(Base):
    __tablename__ = "promos"
    code = Column(String, primary_key=True)
    credits = Column(Float)
    active = Column(Boolean, default=True)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(String, primary_key=True)
    user_id = Column(Integer)
    method = Column(String)
    amount = Column(Float)
    credits = Column(Float)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
