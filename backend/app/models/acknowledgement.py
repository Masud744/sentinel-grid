import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.base import Base


class Acknowledgement(Base):
    __tablename__ = "acknowledgements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    incident = relationship("Incident", back_populates="acknowledgement")
    user = relationship("User", back_populates="acknowledgements")

    # DB Unique constraint ensures atomic single-acknowledgement per incident.
    # Concurrent write attempts for the same incident_id will fail at DB level (409 Conflict), preventing race conditions.
    __table_args__ = (
        UniqueConstraint("incident_id", name="uq_incident_acknowledgement"),
    )
