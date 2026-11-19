"""מתאם את תהליך הקליטה המלא: Adapter -> דה-דופ -> שמירה ב-DB -> תזמון ניתוח
AI (אסינכרוני, דרך jobs.queue). תוצאה: IngestionRun מתועד לשקיפות (סעיף 16)."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.adapters.base import RawMediaItem
from app.adapters.factory import get_adapter
from app.models.ingestion_run import IngestionRun
from app.models.media_item import MediaItem
from app.models.source_connection import SourceConnection
from app.services.dedup_service import resolve_dedup


def run_ingestion(
    db: Session,
    source: SourceConnection,
    extra_config: dict | None = None,
    enqueue_background_analysis: bool = True,
) -> IngestionRun:
    run = IngestionRun(source_connection_id=source.id, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    new_item_ids: list[str] = []
    errors: list[dict] = []

    try:
        adapter = get_adapter(source.source_type)
        config = {**source.config, **(extra_config or {})}
        raw_items: list[RawMediaItem] = adapter.fetch(config)
        run.items_fetched = len(raw_items)

        for raw in raw_items:
            try:
                decision = resolve_dedup(db, source.organization_id, raw)
            except Exception as exc:  # noqa: BLE001
                run.items_rejected += 1
                errors.append({"title": raw.title, "error": str(exc)})
                continue

            if decision.is_exact_duplicate:
                run.items_duplicate += 1
                continue

            item = MediaItem(
                organization_id=source.organization_id,
                source_connection_id=source.id,
                external_id=raw.external_id,
                title=raw.title,
                content=raw.content,
                summary=raw.summary,
                published_at=raw.published_at,
                outlet_name=raw.outlet_name,
                author_name=raw.author_name,
                media_type=raw.media_type,
                url=raw.url,
                keywords=raw.keywords,
                entities=raw.entities,
                exposure_count=raw.exposure_count,
                engagement_count=raw.engagement_count,
                content_hash=decision.content_hash,
                normalized_url=decision.normalized_url,
                dedup_role=decision.role,
                dedup_of_item_id=decision.dedup_of_item_id,
                raw_payload=raw.raw_payload,
            )
            db.add(item)
            db.flush()
            new_item_ids.append(str(item.id))
            run.items_new += 1

        source.last_synced_at = datetime.now(timezone.utc)
        run.status = "succeeded"
    except Exception as exc:  # noqa: BLE001
        run.status = "failed"
        errors.append({"error": str(exc)})

    run.items_pending_analysis = len(new_item_ids)
    run.errors = errors
    run.finished_at = datetime.now(timezone.utc)
    db.commit()

    if new_item_ids and enqueue_background_analysis:
        from app.jobs.queue import enqueue_analysis

        enqueue_analysis(new_item_ids)

    return run
