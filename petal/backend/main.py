"""
Petal Backend - FastAPI application for context management.

Main entry point for the application.
"""


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.routes import health, sessions, memories
from app.services.cache import embedding_cache
from app.services import embeddings
from app.services.task_queue import task_queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Petal Backend",
    description="Context management system with smart copy/paste features",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(memories.router)


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Starting Petal Backend...")

    # Initialize embedding service with cache
    embeddings.embedding_service = embeddings.EmbeddingService(embedding_cache=embedding_cache)
    logger.info("Embedding service initialized with Redis cache")

    # Start background task queue
    await task_queue.start()
    logger.info("Background task queue started")

    logger.info("API documentation available at http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Shutting down Petal Backend...")

    # Stop background task queue
    await task_queue.stop()
    logger.info("Background task queue stopped")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
