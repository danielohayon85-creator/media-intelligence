from datetime import datetime, timedelta, timezone

from app.adapters.base import RawMediaItem
from app.services.dedup_service import compute_content_hash, normalize_url, resolve_dedup


def _raw(**overrides) -> RawMediaItem:
    base = dict(
        external_id="ext-1",
        title="כתבה על הרשות לאכיפה במקרקעין",
        content="תוכן הכתבה",
        summary=None,
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        outlet_name="ynet",
        author_name=None,
        media_type="online",
        url="https://example.test/a?utm=1",
    )
    base.update(overrides)
    return RawMediaItem(**base)


def test_normalize_url_strips_query_and_trailing_slash():
    assert normalize_url("HTTPS://Example.com/Path/?x=1") == "https://example.com/path"
    assert normalize_url(None) is None


def test_content_hash_is_stable_and_whitespace_insensitive():
    h1 = compute_content_hash("כותרת", "תוכן  מלא")
    h2 = compute_content_hash("כותרת", "תוכן מלא")
    assert h1 == h2


def test_first_item_is_original(db, organization):
    decision = resolve_dedup(db, organization.id, _raw())
    assert decision.role == "original"
    assert decision.is_exact_duplicate is False


def test_same_external_id_is_exact_duplicate(db, organization, source_connection):
    from app.models.media_item import MediaItem

    decision = resolve_dedup(db, organization.id, _raw())
    item = MediaItem(
        organization_id=organization.id,
        source_connection_id=source_connection.id,
        external_id="ext-1",
        title="כתבה על הרשות לאכיפה במקרקעין",
        content="תוכן הכתבה",
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        outlet_name="ynet",
        media_type="online",
        url="https://example.test/a",
        content_hash=decision.content_hash,
        normalized_url=decision.normalized_url,
    )
    db.add(item)
    db.commit()

    decision2 = resolve_dedup(db, organization.id, _raw(external_id="ext-1"))
    assert decision2.is_exact_duplicate is True
    assert decision2.role == "duplicate"


def test_same_text_different_outlet_is_reprint_not_duplicate(db, organization, source_connection):
    from app.models.media_item import MediaItem

    original_raw = _raw()
    decision = resolve_dedup(db, organization.id, original_raw)
    item = MediaItem(
        organization_id=organization.id,
        source_connection_id=source_connection.id,
        external_id=original_raw.external_id,
        title=original_raw.title,
        content=original_raw.content,
        published_at=original_raw.published_at,
        outlet_name=original_raw.outlet_name,
        media_type="online",
        url=original_raw.url,
        content_hash=decision.content_hash,
        normalized_url=decision.normalized_url,
    )
    db.add(item)
    db.commit()

    reprint_raw = _raw(
        external_id="ext-2",
        outlet_name="וואלה",
        url="https://walla.test/b",
        published_at=original_raw.published_at + timedelta(hours=5),
    )
    decision2 = resolve_dedup(db, organization.id, reprint_raw)
    assert decision2.is_exact_duplicate is False
    assert decision2.role == "reprint"
    assert decision2.dedup_of_item_id == str(item.id)


def test_same_text_long_gap_is_follow_up(db, organization, source_connection):
    from app.models.media_item import MediaItem

    original_raw = _raw()
    decision = resolve_dedup(db, organization.id, original_raw)
    item = MediaItem(
        organization_id=organization.id,
        source_connection_id=source_connection.id,
        external_id=original_raw.external_id,
        title=original_raw.title,
        content=original_raw.content,
        published_at=original_raw.published_at,
        outlet_name=original_raw.outlet_name,
        media_type="online",
        url=original_raw.url,
        content_hash=decision.content_hash,
        normalized_url=decision.normalized_url,
    )
    db.add(item)
    db.commit()

    follow_up_raw = _raw(
        external_id="ext-3",
        outlet_name="כלכליסט",
        url="https://calcalist.test/c",
        published_at=original_raw.published_at + timedelta(days=10),
    )
    decision2 = resolve_dedup(db, organization.id, follow_up_raw)
    assert decision2.role == "follow_up"
