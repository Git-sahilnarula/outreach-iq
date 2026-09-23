from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
from app.database import get_db
from app.models.startup_profile import StartupProfile
from app.models.portfolio_project import PortfolioProject
from app.schemas.startup_profile import StartupProfileCreate, StartupProfileUpdate, StartupProfileResponse
from app.schemas.portfolio_project import PortfolioProjectCreate, PortfolioProjectResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/profile", response_model=StartupProfileResponse, status_code=status.HTTP_201_CREATED)
def create_startup_profile(
    profile: StartupProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update startup profile"""
    # Check if profile already exists
    existing_profile = db.query(StartupProfile).filter(
        StartupProfile.user_id == current_user.id
    ).first()
    
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Startup profile already exists. Use PUT to update."
        )
    
    # Convert lists to JSON strings for storage
    profile_data = profile.model_dump()
    for field in ['services', 'technical_skills', 'preferred_job_types', 'preferred_industries', 
                  'preferred_locations', 'certifications', 'keywords', 'excluded_keywords']:
        if profile_data.get(field) is not None:
            profile_data[field] = json.dumps(profile_data[field])
    
    new_profile = StartupProfile(user_id=current_user.id, **profile_data)
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    return new_profile

@router.get("/profile", response_model=StartupProfileResponse)
def get_startup_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get startup profile"""
    profile = db.query(StartupProfile).filter(
        StartupProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup profile not found"
        )
    
    return profile

@router.put("/profile", response_model=StartupProfileResponse)
def update_startup_profile(
    profile: StartupProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update startup profile"""
    existing_profile = db.query(StartupProfile).filter(
        StartupProfile.user_id == current_user.id
    ).first()
    
    if not existing_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup profile not found"
        )
    
    # Convert lists to JSON strings for storage
    profile_data = profile.model_dump(exclude_unset=True)
    for field in ['services', 'technical_skills', 'preferred_job_types', 'preferred_industries', 
                  'preferred_locations', 'certifications', 'keywords', 'excluded_keywords']:
        if field in profile_data and profile_data[field] is not None:
            profile_data[field] = json.dumps(profile_data[field])
    
    for field, value in profile_data.items():
        setattr(existing_profile, field, value)
    
    db.commit()
    db.refresh(existing_profile)
    
    return existing_profile

@router.post("/profile/portfolio", response_model=PortfolioProjectResponse, status_code=status.HTTP_201_CREATED)
def add_portfolio_project(
    project: PortfolioProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a portfolio project to startup profile"""
    # Get startup profile
    profile = db.query(StartupProfile).filter(
        StartupProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup profile not found. Create profile first."
        )
    
    # Convert lists to JSON strings for storage
    project_data = project.model_dump()
    for field in ['skills', 'technologies', 'results']:
        if project_data.get(field) is not None:
            project_data[field] = json.dumps(project_data[field])
    
    new_project = PortfolioProject(startup_profile_id=profile.id, **project_data)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return new_project

@router.get("/profile/portfolio", response_model=List[PortfolioProjectResponse])
def get_portfolio_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all portfolio projects for the user"""
    profile = db.query(StartupProfile).filter(
        StartupProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup profile not found"
        )
    
    projects = db.query(PortfolioProject).filter(
        PortfolioProject.startup_profile_id == profile.id
    ).all()
    
    return projects
