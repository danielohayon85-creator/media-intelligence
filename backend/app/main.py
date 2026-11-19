from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import dashboard, demo, ingest, insights, items, organizations, sources
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    import app.models  # noqa: F401  ensures all models are registered on Base

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Media Intelligence API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(organizations.router)
app.include_router(sources.router)
app.include_router(ingest.router)
app.include_router(items.router)
app.include_router(dashboard.router)
app.include_router(insights.router)
app.include_router(demo.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
