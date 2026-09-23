import pytest
from unittest.mock import AsyncMock, patch
from app.models.job import JobStatus
from app.models.proposal import ProposalStatus
from app.schemas.proposal import ProposalGenerated


@pytest.fixture
def auth_headers(client):
    client.post(
        "/api/auth/register",
        json={
            "name": "Proposal Tester",
            "email": "proposal_test@example.com",
            "password": "password123"
        }
    )
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": "proposal_test@example.com",
            "password": "password123"
        }
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_with_job_and_profile(client, auth_headers):
    # Create profile
    client.post(
        "/api/profile",
        headers=auth_headers,
        json={
            "startup_name": "Apex Innovations",
            "description": "High-performance software and AI solutions.",
            "technical_skills": ["Python", "FastAPI", "React", "PyTorch"],
            "services": ["Cloud Architecture", "Full-Stack Development"],
            "minimum_budget": 5000,
            "preferred_budget": 15000,
            "remote_allowed": True
        }
    )

    # Create portfolio project
    proj_res = client.post(
        "/api/profile/portfolio",
        headers=auth_headers,
        json={
            "project_name": "Enterprise Data Platform",
            "description": "Engineered real-time data processing backend.",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "technologies": ["Docker", "Kubernetes", "Redis"],
            "results": ["Reduced latency by 45%", "Scaled to 10k RPS"]
        }
    )
    project_id = proj_res.json()["id"]

    # Create job
    job_res = client.post(
        "/api/jobs/",
        headers=auth_headers,
        json={
            "title": "Senior Backend Architect",
            "company": "Horizon Media",
            "description": "Seeking expert Python/FastAPI consultant to rebuild scalable backend services.",
            "location": "Remote",
            "job_type": "contract",
            "salary_min": 8000,
            "salary_max": 12000
        }
    )
    job_id = job_res.json()["id"]

    return {
        "headers": auth_headers,
        "job_id": job_id,
        "project_id": project_id
    }


def test_generate_proposal_with_mock_ai(client, user_with_job_and_profile):
    """Test generating a proposal draft with mocked AI provider"""
    job_id = user_with_job_and_profile["job_id"]
    headers = user_with_job_and_profile["headers"]
    project_id = user_with_job_and_profile["project_id"]

    mock_generated = ProposalGenerated(
        title="Scalable Python Architecture for Horizon Media",
        content="# Executive Summary\nApex Innovations will engineer a robust backend...",
        cover_letter="Hi Horizon Media team,\n\nWe would love to rebuild your services...",
        estimated_duration="4-6 weeks",
        estimated_budget="$9,000 - $11,000",
        relevant_projects=[project_id]
    )

    with patch('app.api.proposals.get_ai_provider') as mock_get_ai:
        mock_provider = AsyncMock()
        mock_provider.generate_proposal.return_value = mock_generated
        mock_get_ai.return_value = mock_provider

        res = client.post(
            f"/api/jobs/{job_id}/proposals/generate",
            headers=headers,
            json={
                "tone": "technical",
                "custom_instructions": "Focus on high concurrency and Redis caching."
            }
        )

        assert res.status_code == 201
        data = res.json()
        assert data["job_id"] == job_id
        assert data["version"] == 1
        assert data["title"] == "Scalable Python Architecture for Horizon Media"
        assert data["tone"] == "technical"
        assert data["status"] == "DRAFT"
        assert "Executive Summary" in data["content"]
        assert "Horizon Media" in data["cover_letter"]
        assert data["relevant_projects"] == [project_id]

        # Verify Job status updated to PROPOSAL_READY
        job_res = client.get(f"/api/jobs/{job_id}", headers=headers)
        assert job_res.json()["status"] == JobStatus.PROPOSAL_READY.value

        # Verify Notification created
        notif_res = client.get("/api/notifications", headers=headers)
        assert notif_res.json()["unread"] >= 1
        titles = [n["title"] for n in notif_res.json()["notifications"]]
        assert "Proposal Ready" in titles


def test_generate_proposal_increments_version(client, user_with_job_and_profile):
    """Test generating successive proposals increments version number"""
    job_id = user_with_job_and_profile["job_id"]
    headers = user_with_job_and_profile["headers"]

    mock_v1 = ProposalGenerated(
        title="Proposal V1",
        content="Content V1",
        cover_letter="Cover V1",
        estimated_duration="2 weeks",
        estimated_budget="$5,000",
        relevant_projects=[]
    )
    mock_v2 = ProposalGenerated(
        title="Proposal V2",
        content="Content V2",
        cover_letter="Cover V2",
        estimated_duration="3 weeks",
        estimated_budget="$7,000",
        relevant_projects=[]
    )

    with patch('app.api.proposals.get_ai_provider') as mock_get_ai:
        mock_provider = AsyncMock()
        mock_get_ai.return_value = mock_provider

        mock_provider.generate_proposal.return_value = mock_v1
        res1 = client.post(f"/api/jobs/{job_id}/proposals/generate", headers=headers, json={"tone": "professional"})
        assert res1.status_code == 201
        assert res1.json()["version"] == 1

        mock_provider.generate_proposal.return_value = mock_v2
        res2 = client.post(f"/api/jobs/{job_id}/proposals/generate", headers=headers, json={"tone": "conversational"})
        assert res2.status_code == 201
        assert res2.json()["version"] == 2


def test_get_job_proposals(client, user_with_job_and_profile):
    """Test listing all proposals for a job ordered newest version first"""
    job_id = user_with_job_and_profile["job_id"]
    headers = user_with_job_and_profile["headers"]

    with patch('app.api.proposals.get_ai_provider') as mock_get_ai:
        mock_provider = AsyncMock()
        mock_provider.generate_proposal.return_value = ProposalGenerated(
            title="Test", content="Body", cover_letter="Letter", estimated_duration="1w", estimated_budget="$1k"
        )
        mock_get_ai.return_value = mock_provider

        client.post(f"/api/jobs/{job_id}/proposals/generate", headers=headers, json={})
        client.post(f"/api/jobs/{job_id}/proposals/generate", headers=headers, json={})

    res = client.get(f"/api/jobs/{job_id}/proposals", headers=headers)
    assert res.status_code == 200
    proposals = res.json()
    assert len(proposals) == 2
    assert proposals[0]["version"] == 2
    assert proposals[1]["version"] == 1


def test_update_proposal(client, user_with_job_and_profile):
    """Test updating proposal draft content"""
    job_id = user_with_job_and_profile["job_id"]
    headers = user_with_job_and_profile["headers"]

    with patch('app.api.proposals.get_ai_provider') as mock_get_ai:
        mock_provider = AsyncMock()
        mock_provider.generate_proposal.return_value = ProposalGenerated(
            title="Original Title", content="Original Content", cover_letter="Original Letter"
        )
        mock_get_ai.return_value = mock_provider

        create_res = client.post(f"/api/jobs/{job_id}/proposals/generate", headers=headers, json={})
        prop_id = create_res.json()["id"]

    update_res = client.put(
        f"/api/proposals/{prop_id}",
        headers=headers,
        json={
            "title": "Updated Custom Proposal Title",
            "content": "Edited markdown proposal with custom pricing table.",
            "cover_letter": "Short tailored email pitch."
        }
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["title"] == "Updated Custom Proposal Title"
    assert data["content"] == "Edited markdown proposal with custom pricing table."
    assert data["cover_letter"] == "Short tailored email pitch."


def test_approve_and_reject_proposal(client, user_with_job_and_profile):
    """Test approving and rejecting proposals"""
    job_id = user_with_job_and_profile["job_id"]
    headers = user_with_job_and_profile["headers"]

    with patch('app.api.proposals.get_ai_provider') as mock_get_ai:
        mock_provider = AsyncMock()
        mock_provider.generate_proposal.return_value = ProposalGenerated(
            title="Approval Candidate", content="Good content", cover_letter="Good letter"
        )
        mock_get_ai.return_value = mock_provider

        p1 = client.post(f"/api/jobs/{job_id}/proposals/generate", headers=headers, json={}).json()
        p2 = client.post(f"/api/jobs/{job_id}/proposals/generate", headers=headers, json={}).json()

    # Reject p1
    rej_res = client.post(f"/api/proposals/{p1['id']}/reject", headers=headers)
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == ProposalStatus.REJECTED.value

    # Approve p2
    app_res = client.post(f"/api/proposals/{p2['id']}/approve", headers=headers)
    assert app_res.status_code == 200
    assert app_res.json()["status"] == ProposalStatus.APPROVED.value

    # Verify job status changed to PROPOSAL_APPROVED
    job_res = client.get(f"/api/jobs/{job_id}", headers=headers)
    assert job_res.json()["status"] == JobStatus.PROPOSAL_APPROVED.value

    # Verify notification for approval
    notifs = client.get("/api/notifications", headers=headers).json()["notifications"]
    titles = [n["title"] for n in notifs]
    assert "Proposal Approved" in titles


def test_proposal_permissions(client, user_with_job_and_profile):
    """Test that users cannot access another user's proposals"""
    job_id = user_with_job_and_profile["job_id"]
    headers = user_with_job_and_profile["headers"]

    with patch('app.api.proposals.get_ai_provider') as mock_get_ai:
        mock_provider = AsyncMock()
        mock_provider.generate_proposal.return_value = ProposalGenerated(
            title="Private Proposal", content="Secret", cover_letter="Secret"
        )
        mock_get_ai.return_value = mock_provider

        p = client.post(f"/api/jobs/{job_id}/proposals/generate", headers=headers, json={}).json()
        prop_id = p["id"]

    # Register user 2
    client.post(
        "/api/auth/register",
        json={"name": "Attacker", "email": "attacker@example.com", "password": "password123"}
    )
    user2_token = client.post(
        "/api/auth/login",
        json={"email": "attacker@example.com", "password": "password123"}
    ).json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}

    # Attempt to read proposal
    get_res = client.get(f"/api/proposals/{prop_id}", headers=user2_headers)
    assert get_res.status_code == 404

    # Attempt to approve proposal
    app_res = client.post(f"/api/proposals/{prop_id}/approve", headers=user2_headers)
    assert app_res.status_code == 404
