import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, patch
from app.main import app
from app.database import get_db, Base
from app.models.user import User
from app.models.startup_profile import StartupProfile
from app.models.portfolio_project import PortfolioProject
from app.models.job import Job, JobStatus
from app.schemas.job_analysis import JobAnalysisCreate
from app.services.auth import get_password_hash

from tests.conftest import engine, TestingSessionLocal

@pytest.fixture
def auth_token(client):
    # Register and login to get token
    client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    return response.json()["access_token"]

@pytest.fixture
def setup_profile_and_job(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Create startup profile
    profile_response = client.post(
        "/api/profile",
        headers=headers,
        json={
            "startup_name": "Test Startup",
            "description": "AI development company",
            "technical_skills": ["Python", "Machine Learning", "React"],
            "services": ["Web Development", "AI Consulting"],
            "minimum_budget": 50000,
            "preferred_budget": 100000,
            "remote_allowed": True
        }
    )
    
    # Create portfolio project
    client.post(
        "/api/profile/portfolio",
        headers=headers,
        json={
            "project_name": "AI Project",
            "description": "Built an AI system",
            "skills": ["Python", "Machine Learning"],
            "technologies": ["TensorFlow", "FastAPI"]
        }
    )
    
    # Create a job
    job_response = client.post(
        "/api/jobs/",
        headers=headers,
        json={
            "title": "Python AI Developer",
            "company": "AI Corp",
            "description": "We need a Python developer with AI experience for a machine learning project",
            "location": "Remote",
            "job_type": "full-time",
            "salary_min": 80000,
            "salary_max": 120000
        }
    )
    
    return {
        "profile_id": profile_response.json()["id"],
        "job_id": job_response.json()["id"],
        "headers": headers
    }

def test_analyze_job_with_mock_ai(client, setup_profile_and_job):
    """Test job analysis with mocked AI provider"""
    job_id = setup_profile_and_job["job_id"]
    headers = setup_profile_and_job["headers"]
    
    # Mock AI response
    mock_analysis = JobAnalysisCreate(
        can_do=True,
        confidence=0.85,
        match_score=85,
        technical_match=90,
        service_match=85,
        experience_match=80,
        budget_match=80,
        location_match=100,
        reasoning=[
            "Requires Python development",
            "Requires AI/ML experience",
            "Budget matches preferences"
        ],
        missing_requirements=[],
        risks=[],
        recommended_action="REVIEW",
        relevant_portfolio_projects=[1]
    )
    
    # Mock the AI provider
    with patch('app.api.jobs.get_ai_provider') as mock_get_provider:
        mock_provider = AsyncMock()
        mock_provider.analyze_opportunity.return_value = mock_analysis
        mock_get_provider.return_value = mock_provider
        
        # Analyze the job
        response = client.post(f"/api/jobs/{job_id}/analyze", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["match_score"] == 85
        assert data["can_do"] == True
        assert data["recommended_action"] == "REVIEW"
        assert len(data["reasoning"]) == 3

def test_analyze_job_without_profile(client, auth_token):
    """Test that analysis fails without a profile"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Create a job without profile
    job_response = client.post(
        "/api/jobs/",
        headers=headers,
        json={
            "title": "Python Developer",
            "company": "Test Corp",
            "description": "We need a Python developer"
        }
    )
    job_id = job_response.json()["id"]
    
    # Try to analyze without profile
    response = client.post(f"/api/jobs/{job_id}/analyze", headers=headers)
    assert response.status_code == 400
    assert "profile not found" in response.json()["detail"].lower()

def test_matching_threshold(client, setup_profile_and_job):
    """Test that jobs above threshold are marked for review"""
    job_id = setup_profile_and_job["job_id"]
    headers = setup_profile_and_job["headers"]
    
    # Mock high-scoring analysis (above default threshold of 75)
    mock_analysis = JobAnalysisCreate(
        can_do=True,
        confidence=0.90,
        match_score=85,
        technical_match=90,
        service_match=85,
        experience_match=80,
        budget_match=80,
        location_match=100,
        reasoning=["Good match"],
        missing_requirements=[],
        risks=[],
        recommended_action="REVIEW",
        relevant_portfolio_projects=[]
    )
    
    with patch('app.api.jobs.get_ai_provider') as mock_get_provider:
        mock_provider = AsyncMock()
        mock_provider.analyze_opportunity.return_value = mock_analysis
        mock_get_provider.return_value = mock_provider
        
        client.post(f"/api/jobs/{job_id}/analyze", headers=headers)
        
        # Check job status changed to REVIEW_REQUIRED
        job_response = client.get(f"/api/jobs/{job_id}", headers=headers)
        assert job_response.json()["status"] == JobStatus.REVIEW_REQUIRED

def test_low_score_rejection(client, setup_profile_and_job):
    """Test that jobs below threshold are rejected"""
    job_id = setup_profile_and_job["job_id"]
    headers = setup_profile_and_job["headers"]
    
    # Mock low-scoring analysis (below default threshold of 75)
    mock_analysis = JobAnalysisCreate(
        can_do=False,
        confidence=0.50,
        match_score=50,
        technical_match=40,
        service_match=50,
        experience_match=60,
        budget_match=30,
        location_match=100,
        reasoning=["Poor match"],
        missing_requirements=["Missing key skills"],
        risks=["Budget too low"],
        recommended_action="REJECT",
        relevant_portfolio_projects=[]
    )
    
    with patch('app.api.jobs.get_ai_provider') as mock_get_provider:
        mock_provider = AsyncMock()
        mock_provider.analyze_opportunity.return_value = mock_analysis
        mock_get_provider.return_value = mock_provider
        
        client.post(f"/api/jobs/{job_id}/analyze", headers=headers)
        
        # Check job status changed to REJECTED
        job_response = client.get(f"/api/jobs/{job_id}", headers=headers)
        assert job_response.json()["status"] == JobStatus.REJECTED
