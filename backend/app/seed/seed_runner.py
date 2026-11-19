"""מריץ זריעת נתוני הדגמה מלאה: ארגון דמו + מקור demo + קליטה + ניתוח סינכרוני,
כך שהדשבורד מציג תוצאות מיידית בלי להמתין לתור הרקע (סעיף 18 במפרט)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.jobs.analysis_worker import analyze_items_sync
from app.models.organization import Organization
from app.models.source_connection import SourceConnection
from app.seed.demo_data_generator import RELEVANCE_PROFILE
from app.services.ingestion_service import run_ingestion

DEMO_ORG_NAME = "הרשות לאכיפה במקרקעין (הדגמה)"


def get_or_create_demo_organization(db: Session) -> Organization:
    org = db.execute(select(Organization).where(Organization.name == DEMO_ORG_NAME)).scalar_one_or_none()
    if org:
        return org
    org = Organization(
        name=DEMO_ORG_NAME,
        profile_key="real_estate_enforcement",
        relevance_profile=RELEVANCE_PROFILE,
        is_demo=True,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def get_or_create_demo_source(db: Session, organization: Organization) -> SourceConnection:
    source = db.execute(
        select(SourceConnection).where(
            SourceConnection.organization_id == organization.id,
            SourceConnection.source_type == "demo",
        )
    ).scalar_one_or_none()
    if source:
        return source
    source = SourceConnection(
        organization_id=organization.id,
        name="נתוני הדגמה סינתטיים",
        source_type="demo",
        config={"item_count": 450, "seed": 42},
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def seed_demo_data(db: Session) -> dict:
    org = get_or_create_demo_organization(db)
    source = get_or_create_demo_source(db, org)
    run = run_ingestion(db, source, enqueue_background_analysis=False)

    from sqlalchemy import select as _select
    from app.models.media_item import MediaItem

    new_item_ids = [
        str(row.id)
        for row in db.execute(
            _select(MediaItem.id).where(MediaItem.source_connection_id == source.id)
        ).all()
    ]
    analyze_items_sync(new_item_ids)

    return {
        "organization_id": str(org.id),
        "source_connection_id": str(source.id),
        "ingestion_run_id": str(run.id),
        "items_fetched": run.items_fetched,
        "items_new": run.items_new,
        "items_duplicate": run.items_duplicate,
    }
