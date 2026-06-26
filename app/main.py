# app/main.py
"""
Application Entry Point
Creates the FastAPI app, registers routes, and adds global error handling.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routes.api import router

app = FastAPI(
    title="AI Enterprise Assistant",
    description="An LLM-powered assistant that answers employee queries and performs business actions.",
    version="1.0.0",
)

# Register all routes under /api/v1
app.include_router(router, prefix="/api/v1")


# ─── Global Error Handler ─────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred.", "detail": str(exc)},
    )


# ─── Root ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "AI Enterprise Assistant is running.",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
