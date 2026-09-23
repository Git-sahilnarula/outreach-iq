"""
Shared helpers for API routes.

Provides reusable query, serialization, and conversion utilities
to eliminate duplication across jobs, proposals, webhooks, and outreach modules.
"""
import json
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.startup_profile import StartupProfile
from app.models.portfolio_project import PortfolioProject


def get_user_job(db: Session, job_id: int, user_id: int) -> Job:
    """Fetch a job owned by user_id or raise 404."""
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


def get_user_profile(db: Session, user_id: int, *, required: bool = True) -> Optional[StartupProfile]:
    """Fetch the startup profile for a user. Raises 400 if required and missing."""
    profile = db.query(StartupProfile).filter(StartupProfile.user_id == user_id).first()
    if not profile and required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Startup profile not found. Create profile first.",
        )
    return profile


def get_portfolio_projects(db: Session, profile_id: int) -> List[PortfolioProject]:
    """Fetch all portfolio projects for a startup profile."""
    return db.query(PortfolioProject).filter(PortfolioProject.startup_profile_id == profile_id).all()


def _json_load(value: Optional[str]) -> Any:
    """Safely parse a JSON string column, returning [] on None or failure."""
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


def serialize_profile(profile: StartupProfile) -> Dict[str, Any]:
    """Convert a StartupProfile ORM object to a dict suitable for the AI provider."""
    return {
        "startup_name": profile.startup_name,
        "description": profile.description,
        "industry": profile.industry,
        "services": _json_load(profile.services),
        "technical_skills": _json_load(profile.technical_skills),
        "preferred_job_types": _json_load(profile.preferred_job_types),
        "preferred_industries": _json_load(profile.preferred_industries),
        "minimum_budget": float(profile.minimum_budget) if profile.minimum_budget else None,
        "preferred_budget": float(profile.preferred_budget) if profile.preferred_budget else None,
        "preferred_locations": _json_load(profile.preferred_locations),
        "remote_allowed": profile.remote_allowed,
        "team_size": profile.team_size,
        "certifications": _json_load(profile.certifications),
        "keywords": _json_load(profile.keywords),
        "excluded_keywords": _json_load(profile.excluded_keywords),
    }


def serialize_projects(projects: List[PortfolioProject]) -> List[Dict[str, Any]]:
    """Convert a list of PortfolioProject ORM objects to dicts for the AI provider."""
    return [
        {
            "id": p.id,
            "project_name": p.project_name,
            "description": p.description,
            "skills": _json_load(p.skills),
            "technologies": _json_load(p.technologies),
            "results": _json_load(p.results),
        }
        for p in projects
    ]


def serialize_analysis_fields(data: dict) -> dict:
    """JSON-encode the list fields of an analysis result dict in-place and return it."""
    for field in ("reasoning", "missing_requirements", "risks", "relevant_portfolio_projects"):
        if data.get(field) is not None:
            data[field] = json.dumps(data[field])
    return data


# Fields that are stored as JSON strings in StartupProfile / PortfolioProject
PROFILE_JSON_FIELDS = (
    "services", "technical_skills", "preferred_job_types", "preferred_industries",
    "preferred_locations", "certifications", "keywords", "excluded_keywords",
)
PROJECT_JSON_FIELDS = ("skills", "technologies", "results")


def encode_json_fields(data: dict, fields: tuple) -> dict:
    """Convert list values to JSON strings for DB storage, modifying data in-place."""
    for field in fields:
        val = data.get(field)
        if val is not None and not isinstance(val, str):
            data[field] = json.dumps(val)
    return data
