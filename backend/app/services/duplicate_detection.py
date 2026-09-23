import re
from typing import Optional
from sqlalchemy.orm import Session
from app.models.job import Job
import hashlib

def normalize_url(url: Optional[str]) -> Optional[str]:
    """Normalize URL for duplicate detection"""
    if not url:
        return None
    # Remove trailing slashes, convert to lowercase
    url = url.strip().lower().rstrip('/')
    # Remove common tracking parameters
    url = re.sub(r'[?&](utm_[^&]*|ref[^&]*|source[^&]*)', '', url)
    return url

def normalize_title_company(title: str, company: Optional[str]) -> str:
    """Normalize title and company for duplicate detection"""
    title = title.strip().lower()
    company = company.strip().lower() if company else ""
    combined = f"{title}|{company}"
    # Remove extra whitespace
    combined = ' '.join(combined.split())
    return combined

def create_fingerprint(job_data: dict) -> str:
    """Create a deterministic fingerprint for a job"""
    fingerprint_parts = []
    
    # Source job ID if available
    if job_data.get('source_job_id'):
        fingerprint_parts.append(f"source_id:{job_data['source_job_id']}")
    
    # Normalized URL if available
    if job_data.get('url'):
        normalized_url = normalize_url(job_data['url'])
        if normalized_url:
            fingerprint_parts.append(f"url:{normalized_url}")
    
    # Normalized title + company
    if job_data.get('title'):
        title_company = normalize_title_company(
            job_data['title'],
            job_data.get('company')
        )
        fingerprint_parts.append(f"title_company:{title_company}")
    
    # Create hash
    fingerprint_string = "|".join(fingerprint_parts)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()

def check_duplicate(
    db: Session,
    user_id: int,
    job_data: dict
) -> Optional[Job]:
    """
    Check if a job already exists for the user.
    
    Returns the existing job if found, None otherwise.
    """
    # Check by source_job_id if provided
    if job_data.get('source_job_id'):
        existing = db.query(Job).filter(
            Job.user_id == user_id,
            Job.source_job_id == job_data['source_job_id']
        ).first()
        if existing:
            return existing
    
    # Check by normalized URL if provided
    if job_data.get('url'):
        normalized_url = normalize_url(job_data['url'])
        if normalized_url:
            existing = db.query(Job).filter(
                Job.user_id == user_id,
                Job.url == normalized_url
            ).first()
            if existing:
                return existing
    
    # Check by normalized title + company
    if job_data.get('title'):
        title_company = normalize_title_company(
            job_data['title'],
            job_data.get('company')
        )
        existing = db.query(Job).filter(
            Job.user_id == user_id,
            Job.title == job_data['title'],
            Job.company == job_data.get('company')
        ).first()
        if existing:
            return existing
    
    return None
