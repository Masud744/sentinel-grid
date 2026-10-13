import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    role = relationship("Role", back_populates="users", lazy="selectin")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    acknowledgements = relationship("Acknowledgement", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="actor")
