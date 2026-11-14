import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.database.connection import init_db
from app.routes.pipeline import router as pipeline_router
from app.routes.logs import router as logs_router
from app.routes.rejected import router as rejected_router
from app.routes.metrics import router as metrics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield


app = FastAPI(
    title="Application Log Analytics & Monitoring Platform API",
    version="1.0.0",
    description="Production-grade Data Engineering pipeline and analytics API for structured and semi-structured log intelligence.",
    lifespan=lifespan,
)

# Ensure database tables are initialized at import time as well
init_db()

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(pipeline_router)
app.include_router(logs_router)
app.include_router(rejected_router)
app.include_router(metrics_router)


@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "Application Log Analytics Backend",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


@app.get("/api/info", tags=["System"])
def system_info():
    return {
        "architecture": "Three-Tier Architecture (React.js + FastAPI + PostgreSQL/SQLite)",
        "supported_formats": ["CSV", "JSON (Array & Lines)", "Semi-structured Text/Log"],
        "normalizations": [
            "Timestamps to UTC ISO-8601",
            "Severities to [INFO, WARNING, ERROR, CRITICAL]",
            "Deterministic event IDs",
            "API latency (ms) & error rate % calculations"
        ]
    }


# Mount production frontend build if present
dist_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if dist_path.exists():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "127.0.0.1")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
