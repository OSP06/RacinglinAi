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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting RacingLineAI API...")
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
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "ml_models": "loaded"
    }
