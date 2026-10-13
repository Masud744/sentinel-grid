import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id = Column(String(36), ForeignKey("zones.id", ondelete="RESTRICT"), nullable=False)
    sensor_type = Column(String(50), nullable=False)  # 'fire', 'gas', 'water', 'occupancy'
    unit = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    zone = relationship("Zone", back_populates="sensors")
