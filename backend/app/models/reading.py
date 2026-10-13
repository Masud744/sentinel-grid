from datetime import datetime, timezone
from sqlalchemy import Column, Integer, BigInteger, Float, String, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from app.database.base import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    zone_id = Column(String(36), ForeignKey("zones.id", ondelete="RESTRICT"), nullable=False, index=True)
    sequence_id = Column(BigInteger, nullable=False)
    fire_signal = Column(Integer, nullable=False, default=0)
    gas_level_raw = Column(Float, nullable=False, default=0.0)
    water_level_raw = Column(Float, nullable=False, default=0.0)
    occupancy_raw = Column(Integer, nullable=False, default=0)
    computed_risk_score = Column(Float, nullable=False, default=0.0)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    zone = relationship("Zone", back_populates="readings")

    __table_args__ = (
        Index("idx_sensor_readings_zone_time", "zone_id", "received_at"),
        Index("idx_sensor_readings_seq", "zone_id", "sequence_id"),
    )
