"""
CV Maker API Application

FastAPI application for generating tailored CVs based on job descriptions.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.cv import router as cv_router
from src.api.v1.index import router as index_router
from src.core.logger import setup_root_logger

# Setup logging
logger = setup_root_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    logger.info("Starting CV Maker API application")
    yield
    logger.info("Shutting down CV Maker API application")


# Create FastAPI application
app = FastAPI(
    title="CV Maker API",
    description="API for generating tailored CVs based on job descriptions",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cv_router)
app.include_router(index_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "CV Maker API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
