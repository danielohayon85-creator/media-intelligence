import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://media:media@localhost:5432/media_intelligence_test"
)
# חייב להיקבע לפני ייבוא app.core.config (Settings נטען פעם אחת, בזמן import)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["AI_PROVIDER"] = "mock"

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.db.base import Base  # noqa: E402
import app.models  # noqa: E402,F401

_engine = create_engine(TEST_DATABASE_URL)
_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def db():
    session = _TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()


@pytest.fixture
def organization(db):
    from app.models.organization import Organization

    org = Organization(
        name="Test Org",
        profile_key="generic",
        relevance_profile={
            "direct_keywords": ["הרשות לאכיפה במקרקעין"],
            "indirect_keywords": ["צו הריסה"],
            "background_keywords": ["תכנון ובנייה"],
        },
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app as fastapi_app

    with TestClient(fastapi_app) as test_client:
        yield test_client


@pytest.fixture
def source_connection(db, organization):
    from app.models.source_connection import SourceConnection

    source = SourceConnection(
        organization_id=organization.id,
        name="Test Source",
        source_type="demo",
        config={},
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source
