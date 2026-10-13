import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base


class Zone(Base):
    __tablename__ = "zones"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    lab_type = Column(String(50), nullable=False)  # 'iot_lab', 'server_room', 'ds_lab'
    api_key = Column(String(128), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    sensors = relationship("Sensor", back_populates="zone", cascade="all, delete-orphan")
    readings = relationship("SensorReading", back_populates="zone")
    incidents = relationship("Incident", back_populates="zone")
