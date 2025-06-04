# db.py

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# SQLite DB for local use. Change if using PostgreSQL or other DB for Streamlit Cloud.
SQLALCHEMY_DATABASE_URL = "sqlite:///./biofeedback.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class BiofeedbackLog(Base):
    __tablename__ = "biofeedback_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_id = Column(String)
    app_id = Column(String)
    heart_rate = Column(Integer)
    hrv = Column(Integer)
    stress = Column(Integer)
    state = Column(String)
    qos_level = Column(String)
    bandwidth = Column(Float)
    latency = Column(Float)
    policy = Column(String)
    note = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Create tables if not exist
Base.metadata.create_all(bind=engine)
