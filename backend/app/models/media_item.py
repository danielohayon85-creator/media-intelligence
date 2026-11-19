import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Text, Integer, func, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MediaItem(Base):
    """פריט תקשורתי בודד, כפי שנקלט ממקור (ללא שינוי) — סעיף 3 במפרט.
    dedup_role ו-dedup_of_item_id מנהלים הבחנה בין כתבה מקורית, כפילות,
    ציטוט חוזר (reprint) והמשך סיפור (follow_up), כנדרש במפרט: אין לספור
    הפצה חוזרת כסיפור עיתונאי חדש."""

    __tablename__ = "media_items"
    __table_args__ = (
        Index("ix_media_items_org_published", "organization_id", "published_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    source_connection_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_connections.id"))

    external_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    outlet_name: Mapped[str] = mapped_column(String(255))
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    media_type: Mapped[str] = mapped_column(String(50))  # online|print|radio|tv|social
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    entities: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    exposure_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    engagement_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    normalized_url: Mapped[str | None] = mapped_column(String(1000), nullable=True, index=True)

    dedup_role: Mapped[str] = mapped_column(String(20), default="original")  # original|duplicate|reprint|follow_up
    dedup_of_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_items.id"), nullable=True
    )

    raw_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    analysis: Mapped["AnalysisResult | None"] = relationship(
        "AnalysisResult", uselist=False, back_populates="media_item"
    )
