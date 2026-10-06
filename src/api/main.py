from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager

from src.utilities.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for the FastAPI application.
    """
    logger.info("Starting up FastAPI application")
    # Initialize connection pools or ML model loading here
    yield
    logger.info("Shutting down FastAPI application")
    # Cleanup resources here

from .routes import router as v1_router

app = FastAPI(
    title="Real-Time Data Intelligence API",
    description="Serving predictions and low-latency queries over Gold data.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(v1_router)

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "data-intelligence-api"}
