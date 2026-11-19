"""מניעת כפילויות ומעקב סיקור חוזר — הלוגיקה הקריטית ביותר במפרט (סעיף 3:
'אין לספור הפצה חוזרת כאילו מדובר בהכרח בסיפור עיתונאי חדש'). ל-MVP: היוריסטיקה
דטרמיניסטית מבוססת מזהה חיצוני, URL מנורמל ודמיון טקסטואלי — לא AI, כדי
שהתוצאה תהיה שקופה וניתנת לבדיקה."""

import hashlib
import re
from dataclasses import dataclass
from datetime import timedelta
from difflib import SequenceMatcher
from urllib.parse import urlparse, urlunparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.base import RawMediaItem
from app.models.media_item import MediaItem

SIMILARITY_THRESHOLD = 0.82
REPRINT_WINDOW_HOURS = 48
LOOKBACK_DAYS = 14


def normalize_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url.strip().lower())
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", ""))


def compute_content_hash(title: str, content: str | None) -> str:
    normalized = re.sub(r"\s+", " ", f"{title} {content or ''}".strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


@dataclass
class DedupDecision:
    is_exact_duplicate: bool
    role: str  # original | reprint | follow_up
    dedup_of_item_id: str | None
    content_hash: str
    normalized_url: str | None


def resolve_dedup(db: Session, organization_id, raw: RawMediaItem) -> DedupDecision:
    content_hash = compute_content_hash(raw.title, raw.content)
    norm_url = normalize_url(raw.url)

    # 1. כפילות מדויקת: external_id זהה בתוך הארגון
    if raw.external_id:
        existing = db.execute(
            select(MediaItem).where(
                MediaItem.organization_id == organization_id,
                MediaItem.external_id == raw.external_id,
            )
        ).scalar_one_or_none()
        if existing:
            return DedupDecision(True, "duplicate", str(existing.id), content_hash, norm_url)

    # 2. כפילות מדויקת: URL מנורמל זהה
    if norm_url:
        existing = db.execute(
            select(MediaItem).where(
                MediaItem.organization_id == organization_id,
                MediaItem.normalized_url == norm_url,
            )
        ).scalar_one_or_none()
        if existing:
            return DedupDecision(True, "duplicate", str(existing.id), content_hash, norm_url)

    # 3. כפילות מדויקת: content_hash זהה מאותו כלי תקשורת (אותה הודעה
    #    שנקלטה פעמיים). אם הטקסט זהה אך הכלי תקשורת שונה — זה ציטוט חוזר
    #    (reprint) ולא כפילות קליטה, ולכן מטופל בשלב 4 ולא נדחה כאן.
    existing = db.execute(
        select(MediaItem).where(
            MediaItem.organization_id == organization_id,
            MediaItem.content_hash == content_hash,
            MediaItem.outlet_name == raw.outlet_name,
        )
    ).scalar_one_or_none()
    if existing:
        return DedupDecision(True, "duplicate", str(existing.id), content_hash, norm_url)

    # 4. דמיון תוכני — reprint (אותו סיפור, כלי תקשורת אחר, חלון זמן קצר)
    #    או follow_up (סיפור חוזר אחרי פער זמן ניכר)
    lookback_start = raw.published_at - timedelta(days=LOOKBACK_DAYS)
    candidates = db.execute(
        select(MediaItem).where(
            MediaItem.organization_id == organization_id,
            MediaItem.published_at >= lookback_start,
            MediaItem.published_at <= raw.published_at,
        )
    ).scalars().all()

    best_match: MediaItem | None = None
    best_score = 0.0
    for candidate in candidates:
        score = _text_similarity(raw.title, candidate.title)
        if score > best_score:
            best_score = score
            best_match = candidate

    if best_match and best_score >= SIMILARITY_THRESHOLD:
        root_id = str(best_match.dedup_of_item_id or best_match.id)
        gap = raw.published_at - best_match.published_at
        role = "reprint" if gap <= timedelta(hours=REPRINT_WINDOW_HOURS) else "follow_up"
        return DedupDecision(False, role, root_id, content_hash, norm_url)

    return DedupDecision(False, "original", None, content_hash, norm_url)
