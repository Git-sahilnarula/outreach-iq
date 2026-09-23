from datetime import datetime, timezone

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine, init_db
from app.api import auth, startup_profile, jobs, gmail, notifications, proposals, outreach, linkedin, webhooks

init_db()

app = FastAPI(
    title="Outreach IQ",
    description="AI-powered freelance/job opportunity discovery and outreach assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(startup_profile.router, prefix="/api", tags=["Startup Profile"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(gmail.router, prefix="/api/gmail", tags=["Gmail"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(proposals.router, prefix="/api", tags=["Proposals"])
app.include_router(outreach.router, prefix="/api", tags=["Outreach"])
app.include_router(linkedin.router, prefix="/api", tags=["LinkedIn"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])


@app.get("/")
def root():
    return {"message": "Outreach IQ API", "version": "1.0.0"}


@app.get("/api/health")
async def health_check():
    """System health check endpoint with database and AI telemetry."""
    checks = {"database": "unknown", "ai_provider": "unknown"}

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"unreachable: {e}"

    if settings.AI_PROVIDER == "ollama":
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                checks["ai_provider"] = "connected" if res.status_code == 200 else f"http_{res.status_code}"
        except Exception:
            checks["ai_provider"] = "unreachable (local ollama offline)"
    else:
        checks["ai_provider"] = f"configured ({settings.AI_PROVIDER})"

    overall = "healthy" if checks["database"] == "connected" else "degraded"
    return {
        "status": overall,
        "service": "outreach-iq-api",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
