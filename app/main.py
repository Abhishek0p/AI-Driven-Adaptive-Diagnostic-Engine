"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import connect_db, close_db
from app.routers import questions, session, insights


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: connect to DB on startup, close on shutdown."""
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="Adaptive Diagnostic Engine",
    description=(
        "A 1-Dimension Adaptive Testing system that determines student "
        "proficiency using IRT (Item Response Theory). Dynamically selects "
        "GRE-style questions based on previous answers and generates "
        "AI-powered personalized study plans."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(questions.router)
app.include_router(session.router)
app.include_router(insights.router)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": "Adaptive Diagnostic Engine",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }
