from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.models.batch_event import BatchEvent  # noqa: F401 — ensure table is created
from app.routers import admin, batches, seed_inventory, trace


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="TraceGreens",
    description="Microgreens batch management and traceability system",
    version="0.2.0",
    lifespan=lifespan,
)

# JSON API routers (keep for programmatic access)
app.include_router(seed_inventory.router)
app.include_router(batches.router)

# Admin HTML interface (password-protected)
app.include_router(admin.router)

# Public website + trace portal (no auth required)
app.include_router(trace.router)
