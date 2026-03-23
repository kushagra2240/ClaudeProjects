from sqlalchemy import Column, Integer, Float, Date, DateTime, String
from backend.database import Base


class DailySteps(Base):
    __tablename__ = "daily_steps"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True)
    steps = Column(Integer)
    calories = Column(Float)
    active_minutes = Column(Integer)
    source = Column(String)


class HeartRate(Base):
    __tablename__ = "heart_rate"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, unique=True)
    bpm = Column(Integer, nullable=False)
    source = Column(String)


class SleepRecord(Base):
    __tablename__ = "sleep_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True)
    total_minutes = Column(Integer)
    deep_minutes = Column(Integer)
    light_minutes = Column(Integer)
    rem_minutes = Column(Integer)
    awake_minutes = Column(Integer)
    source = Column(String)
