"""
RacingLineAI FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.routers import races, predictions, circuits, telemetry
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _auto_import_csvs():
    """
    On startup, scan data/processed/ for any all_races_combined_<year>.csv files
    and import seasons that are not yet in the database.
    Silently skips if the data directory doesn't exist (e.g. local dev without data).
    """
    import os, re
    from pathlib import Path
    from sqlalchemy.orm import sessionmaker
    from app.core.database import engine
    from app.models.database import Season

    data_dir = Path("data/processed")
    if not data_dir.exists():
        return

    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    for csv_file in sorted(data_dir.glob("all_races_combined_*.csv")):
        m = re.search(r"all_races_combined_(\d{4})\.csv", csv_file.name)
        if not m:
            continue
        year = int(m.group(1))

        db = SessionLocal()
        try:
            season = db.query(Season).filter(Season.year == year).first()
            if season and db.execute(
                __import__("sqlalchemy").text(
                    "SELECT COUNT(*) FROM races WHERE season_id = :sid"
                ),
                {"sid": season.id},
            ).scalar() > 0:
                logger.info(f"Season {year} already in DB — skipping auto-import")
                continue

            logger.info(f"Auto-importing season {year} from {csv_file} …")
            from scripts.import_csv_to_db import import_season_data
            import_season_data(str(csv_file), db, year)
            logger.info(f"Season {year} import complete")
        except Exception as e:
            logger.error(f"Auto-import failed for {csv_file}: {e}")
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting RacingLineAI API...")
    # Auto-import any new season CSVs present on disk
    try:
        _auto_import_csvs()
    except Exception as e:
        logger.warning(f"Auto-import step failed (non-fatal): {e}")

    # Load ML models on startup
    from app.services.ml_service import MLService
    ml_service = MLService()
    await ml_service.load_models()
    app.state.ml_service = ml_service
    logger.info("ML models loaded successfully")

    yield

    logger.info("Shutting down RacingLineAI API...")


# Initialize FastAPI app
app = FastAPI(
    title="RacingLineAI API",
    description="Advanced F1 Analytics & Prediction API",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(races.router, prefix="/api/races", tags=["races"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(circuits.router, prefix="/api/circuits", tags=["circuits"])
app.include_router(telemetry.router, prefix="/api/telemetry", tags=["telemetry"])


@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    """Health check endpoint"""
    return {
        "name": "RacingLineAI API",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Detailed health check — actually tests DB connection"""
    from sqlalchemy import text
    from app.core.database import engine
    db_status = "unknown"
    db_error = None
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = "error"
        db_error = str(e)

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "database_error": db_error,
        "database_url_prefix": str(settings.DATABASE_URL)[:40],
        "ml_models": "loaded"
    }
