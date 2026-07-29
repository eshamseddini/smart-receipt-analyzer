from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.api.routes.analytics import router as analytics_router
from app.api.routes.health import router as health_router
from app.api.routes.receipts import router as receipts_router
from app.core.config import settings
from app.db.database import Base, engine
from app.models.receipt import (
    Receipt,  # noqa: F401 -- registers the model with Base.metadata before create_all()
)

Base.metadata.create_all(bind=engine)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Smart Receipt Analyzer",
    description="A FastAPI application for analyzing receipts using OCR and AI models.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(receipts_router, prefix="/api/receipts", tags=["Receipts"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
