import pytest
from unittest.mock import patch
from app.models.job import JobStatus
from app.models.outreach import OutreachStatus
from app.models.gmail_token import GmailToken
from tests.conftest import TestingSessionLocal


@pytest.fixture
def auth_headers(client):
    client.post(
        "/api/auth/register",
        json={"name": "Outreach Tester", "email": "outreach_tester@example.com", "password": "password123"}
    )
    res = client.post(
        "/api/auth/login",
        json={"email": "outreach_tester@example.com", "password": "password123"}
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def job_setup(client, auth_headers):
    # Create profile
    client.post(
        "/api/profile",
        headers=auth_headers,
        json={
            "startup_name": "CloudNine Solutions",
            "description": "Specialized cloud solutions.",
            "technical_skills": ["Python", "AWS", "FastAPI"],
            "services": ["Cloud Architecture"],
            "remote_allowed": True
        }
    )

    # Create job
    job_res = client.post(
        "/api/jobs/",
        headers=auth_headers,
        json={
            "title": "Lead Cloud Engineer",
            "company": "NextGen Media",
            "description": "Need cloud engineer to lead migration to AWS and optimize microservices.",
            "location": "Remote",
            "job_type": "contract"
        }
    )
    return {
        "headers": auth_headers,
        "job_id": job_res.json()["id"]
    }


def test_create_outreach_draft(client, job_setup):
    """Test creating an outreach draft linked to a job"""
    job_id = job_setup["job_id"]
    headers = job_setup["headers"]

    res = client.post(
        f"/api/jobs/{job_id}/outreach/draft",
        headers=headers,
        json={
            "recipient_email": "hiring@nextgenmedia.com",
            "recipient_name": "Sarah Connor",
            "subject": "Proposal for Lead Cloud Engineer role",
            "body": "Hi Sarah,\n\nI saw your opening and wanted to reach out..."
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["job_id"] == job_id
    assert data["recipient_email"] == "hiring@nextgenmedia.com"
    assert data["status"] == OutreachStatus.DRAFT.value
    assert data["sent_at"] is None


def test_get_job_outreach_history(client, job_setup):
    """Test retrieving outreach history for a job"""
    job_id = job_setup["job_id"]
    headers = job_setup["headers"]

    client.post(
        f"/api/jobs/{job_id}/outreach/draft",
        headers=headers,
        json={"recipient_email": "lead1@nextgen.com", "subject": "Draft 1", "body": "Body 1"}
    )
    client.post(
        f"/api/jobs/{job_id}/outreach/draft",
        headers=headers,
        json={"recipient_email": "lead2@nextgen.com", "subject": "Draft 2", "body": "Body 2"}
    )

    res = client.get(f"/api/jobs/{job_id}/outreach", headers=headers)
    assert res.status_code == 200
    records = res.json()
    assert len(records) == 2


def test_update_outreach_draft(client, job_setup):
    """Test updating draft fields"""
    job_id = job_setup["job_id"]
    headers = job_setup["headers"]

    draft = client.post(
        f"/api/jobs/{job_id}/outreach/draft",
        headers=headers,
        json={"recipient_email": "old@example.com", "subject": "Old Subject", "body": "Old Body"}
    ).json()

    res = client.put(
        f"/api/outreach/{draft['id']}",
        headers=headers,
        json={
            "recipient_email": "new_lead@nextgenmedia.com",
            "subject": "Revised Subject",
            "body": "Updated pitch message..."
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["recipient_email"] == "new_lead@nextgenmedia.com"
    assert data["subject"] == "Revised Subject"


def test_send_outreach_requires_confirmation(client, job_setup):
    """Test that confirm_send=False is rejected"""
    job_id = job_setup["job_id"]
    headers = job_setup["headers"]

    res = client.post(
        f"/api/jobs/{job_id}/outreach/send",
        headers=headers,
        json={
            "recipient_email": "ceo@example.com",
            "subject": "Test",
            "body": "Body",
            "confirm_send": False
        }
    )
    assert res.status_code == 400
    assert "Human approval required" in res.json()["detail"]


def test_send_outreach_requires_gmail_connected(client, job_setup):
    """Test sending fails if Gmail is not connected for the user"""
    job_id = job_setup["job_id"]
    headers = job_setup["headers"]

    res = client.post(
        f"/api/jobs/{job_id}/outreach/send",
        headers=headers,
        json={
            "recipient_email": "lead@company.com",
            "subject": "Proposal",
            "body": "Hello",
            "confirm_send": True
        }
    )
    assert res.status_code == 400
    assert "Gmail account is not connected" in res.json()["detail"]


def test_send_outreach_success_with_mock_gmail(client, job_setup):
    """Test sending an outreach email when Gmail is connected"""
    job_id = job_setup["job_id"]
    headers = job_setup["headers"]

    with patch('app.api.outreach.gmail_client.is_connected', return_value=True), \
         patch('app.api.outreach.gmail_client.send_email', return_value={"id": "msg_abc123", "threadId": "th_xyz789"}):

        res = client.post(
            f"/api/jobs/{job_id}/outreach/send",
            headers=headers,
            json={
                "recipient_email": "cto@nextgenmedia.com",
                "recipient_name": "Alex Vance",
                "subject": "Cloud Engineering Consulting — CloudNine",
                "body": "Hi Alex,\n\nWe specialize in high-throughput AWS migrations...",
                "confirm_send": True
            }
        )

        assert res.status_code == 200
        data = res.json()
        assert data["status"] == OutreachStatus.SENT.value
        assert data["gmail_message_id"] == "msg_abc123"
        assert data["sent_at"] is not None

        # Verify Job status updated to CONTACTED
        job_res = client.get(f"/api/jobs/{job_id}", headers=headers)
        assert job_res.json()["status"] == JobStatus.CONTACTED.value

        # Verify Notification generated
        notifs = client.get("/api/notifications", headers=headers).json()["notifications"]
        titles = [n["title"] for n in notifs]
        assert "Outreach Email Sent" in titles


def test_cannot_edit_sent_outreach(client, job_setup):
    """Test that already sent messages cannot be modified"""
    job_id = job_setup["job_id"]
    headers = job_setup["headers"]

    with patch('app.api.outreach.gmail_client.is_connected', return_value=True), \
         patch('app.api.outreach.gmail_client.send_email', return_value={"id": "msg_999", "threadId": "th_999"}):

        sent = client.post(
            f"/api/jobs/{job_id}/outreach/send",
            headers=headers,
            json={
                "recipient_email": "team@test.com",
                "subject": "Subject",
                "body": "Body",
                "confirm_send": True
            }
        ).json()

    res = client.put(
        f"/api/outreach/{sent['id']}",
        headers=headers,
        json={"subject": "Attempt to edit sent email"}
    )
    assert res.status_code == 400
    assert "Cannot edit an email that has already been dispatched" in res.json()["detail"]


def test_delete_outreach_draft(client, job_setup):
    """Test deleting an unsent draft"""
    job_id = job_setup["job_id"]
    headers = job_setup["headers"]

    draft = client.post(
        f"/api/jobs/{job_id}/outreach/draft",
        headers=headers,
        json={"recipient_email": "todelete@test.com", "subject": "Delete me", "body": "Body"}
    ).json()

    del_res = client.delete(f"/api/outreach/{draft['id']}", headers=headers)
    assert del_res.status_code == 200

    # Ensure it's gone
    get_res = client.get(f"/api/outreach/{draft['id']}", headers=headers)
    assert get_res.status_code == 404
