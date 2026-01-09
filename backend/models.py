from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    credits = Column(Float, default=1.0)   # 1 free credit on join


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
