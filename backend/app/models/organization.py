import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Organization(Base):
    """ארגון עם פרופיל רלוונטיות (סעיף 17 במפרט): מילות מפתח ונושאי עניין
    המשמשים את מנוע הסיווג לקביעת רלוונטיות ישירה/עקיפה/רקע/לא-רלוונטי."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    profile_key: Mapped[str] = mapped_column(String(100), default="generic")
    # {"direct_keywords": [...], "indirect_keywords": [...], "background_keywords": [...]}
    relevance_profile: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_demo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
