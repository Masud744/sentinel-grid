import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from app.database.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id = Column(String(36), ForeignKey("zones.id", ondelete="RESTRICT"), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    state = Column(String(20), nullable=False)  # 'WARNING', 'CRITICAL', 'RESOLVED'
    cause = Column(String(255), nullable=False)
    opened_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    zone = relationship("Zone", back_populates="incidents")
    acknowledgement = relationship("Acknowledgement", back_populates="incident", uselist=False, cascade="all, delete-orphan")

    # Composite Index Explanation:
    # `idx_incidents_state_opened` optimizes querying incidents filtered by state ('CRITICAL', 'RESOLVED')
    # ordered by `opened_at` (e.g., retrieving active priority queue or incidents opened in the last 24h).
    # Since `state` has low cardinality and `opened_at` is monotonically increasing, PostgreSQL B-Tree
    # can immediately narrow down to matching states and slice the timestamp range efficiently.
    __table_args__ = (
        Index("idx_incidents_state_opened", "state", "opened_at"),
    )
