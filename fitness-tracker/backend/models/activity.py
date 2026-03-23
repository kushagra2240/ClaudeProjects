from sqlalchemy import Column, Integer, String, Float, Date, DateTime, JSON, UniqueConstraint
from sqlalchemy.sql import func
from backend.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)          # "runkeeper" | "mi_fitness"
    date = Column(Date, nullable=False)
    activity_type = Column(String, nullable=False)   # "run" | "walk" | "cycle" | etc.
    duration_seconds = Column(Integer)
    distance_meters = Column(Float)
    avg_heart_rate = Column(Integer)
    calories = Column(Float)
    gpx_points = Column(JSON)                        # [{lat, lon, ele, time, hr}, ...]
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("source", "date", "duration_seconds", name="uq_activity"),
    )
