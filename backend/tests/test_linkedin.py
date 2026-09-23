import pytest
from unittest.mock import patch
from app.models.job import JobStatus


@pytest.fixture
def linkedin_auth_headers(client):
    client.post(
        "/api/auth/register",
        json={"name": "LinkedIn Tester", "email": "li_tester@example.com", "password": "password123"}
    )
    res = client.post(
        "/api/auth/login",
        json={"email": "li_tester@example.com", "password": "password123"}
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def linkedin_job_setup(client, linkedin_auth_headers):
    # Create profile
    client.post(
        "/api/profile",
        headers=linkedin_auth_headers,
        json={
            "startup_name": "Apex Dev Studio",
            "description": "High-end React and AI engineering.",
            "technical_skills": ["React", "TypeScript", "Python"],
            "services": ["Custom Fullstack Apps", "AI Integrations"],
            "remote_allowed": True
        }
    )

    # Create job
    job_res = client.post(
        "/api/jobs/",
        headers=linkedin_auth_headers,
        json={
            "title": "Principal Frontend Architect",
            "company": "FinTech Prime",
            "description": "Seeking expert frontend architect to build high-speed analytics dashboards.",
            "location": "San Francisco, CA / Remote",
            "job_type": "contract"
        }
    )
    return {
        "headers": linkedin_auth_headers,
        "job_id": job_res.json()["id"]
    }


def test_generate_linkedin_messages_with_mock_ai(client, linkedin_job_setup):
    """Test generating LinkedIn connection note and InMail with mocked AI response"""
    job_id = linkedin_job_setup["job_id"]
    headers = linkedin_job_setup["headers"]

    mock_generated = {
        "connection_note": "Hi Sarah, saw FinTech Prime's search for a Frontend Architect. At Apex Dev Studio, we've built similar ultra-fast React dashboards. Would love to connect and share notes!",
        "inmail_subject": "Frontend Architecture for FinTech Prime's Dashboards",
        "inmail_body": "Hi Sarah,\n\nI noticed FinTech Prime is expanding its frontend architecture initiatives...\n\nBest,\nApex Dev Studio"
    }

    with patch("app.ai.ollama_provider.OllamaProvider.generate_linkedin_messages", return_value=mock_generated):
        res = client.post(
            f"/api/jobs/{job_id}/linkedin/generate",
            headers=headers,
            json={
                "recipient_name": "Sarah Connor",
                "recipient_role": "VP of Engineering",
                "recipient_profile_url": "https://linkedin.com/in/sarah-connor",
                "tone": "value_first",
                "custom_instructions": "Highlight dashboard performance optimization"
            }
        )
        assert res.status_code == 200
        data = res.json()
        assert data["job_id"] == job_id
        assert data["recipient_name"] == "Sarah Connor"
        assert data["recipient_role"] == "VP of Engineering"
        assert data["recipient_profile_url"] == "https://linkedin.com/in/sarah-connor"
        assert data["tone"] == "value_first"
        assert len(data["connection_note"]) <= 300
        assert data["connection_note"] == mock_generated["connection_note"]
        assert data["inmail_subject"] == mock_generated["inmail_subject"]
        assert data["status"] == "GENERATED"


def test_generate_linkedin_messages_fallback(client, linkedin_job_setup):
    """Test fallback template generation when AI provider raises an error"""
    job_id = linkedin_job_setup["job_id"]
    headers = linkedin_job_setup["headers"]

    # When Ollama is unreachable, provider fallback triggers
    res = client.post(
        f"/api/jobs/{job_id}/linkedin/generate",
        headers=headers,
        json={
            "recipient_name": "David Miller",
            "recipient_role": "CTO",
            "tone": "direct"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["connection_note"]) <= 300
    assert "David" in data["connection_note"] or "FinTech Prime" in data["connection_note"]
    assert data["inmail_subject"]
    assert data["inmail_body"]


def test_get_job_linkedin_messages(client, linkedin_job_setup):
    """Test fetching all generated LinkedIn messages for a job"""
    job_id = linkedin_job_setup["job_id"]
    headers = linkedin_job_setup["headers"]

    # Generate one message
    client.post(
        f"/api/jobs/{job_id}/linkedin/generate",
        headers=headers,
        json={"recipient_name": "Alex Vance", "tone": "networking"}
    )

    res = client.get(f"/api/jobs/{job_id}/linkedin", headers=headers)
    assert res.status_code == 200
    messages = res.json()
    assert len(messages) >= 1
    assert messages[0]["recipient_name"] == "Alex Vance"


def test_update_linkedin_message(client, linkedin_job_setup):
    """Test editing LinkedIn message details"""
    job_id = linkedin_job_setup["job_id"]
    headers = linkedin_job_setup["headers"]

    gen_res = client.post(
        f"/api/jobs/{job_id}/linkedin/generate",
        headers=headers,
        json={"recipient_name": "John Doe", "tone": "direct"}
    )
    msg_id = gen_res.json()["id"]

    updated_note = "Custom revised connection note under 300 characters!"
    update_res = client.put(
        f"/api/linkedin/{msg_id}",
        headers=headers,
        json={
            "recipient_name": "Johnathan Doe",
            "connection_note": updated_note,
            "inmail_subject": "Revised InMail Subject"
        }
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["recipient_name"] == "Johnathan Doe"
    assert updated_data["connection_note"] == updated_note
    assert updated_data["inmail_subject"] == "Revised InMail Subject"


def test_update_linkedin_note_too_long(client, linkedin_job_setup):
    """Test that connection notes exceeding 300 characters are rejected with 400"""
    job_id = linkedin_job_setup["job_id"]
    headers = linkedin_job_setup["headers"]

    gen_res = client.post(
        f"/api/jobs/{job_id}/linkedin/generate",
        headers=headers,
        json={"recipient_name": "John Doe"}
    )
    msg_id = gen_res.json()["id"]

    too_long_note = "A" * 301
    bad_res = client.put(
        f"/api/linkedin/{msg_id}",
        headers=headers,
        json={"connection_note": too_long_note}
    )
    assert bad_res.status_code in (400, 422)


def test_mark_linkedin_sent(client, linkedin_job_setup):
    """Test marking outreach as sent on LinkedIn, verifying job transitions to CONTACTED"""
    job_id = linkedin_job_setup["job_id"]
    headers = linkedin_job_setup["headers"]

    gen_res = client.post(
        f"/api/jobs/{job_id}/linkedin/generate",
        headers=headers,
        json={"recipient_name": "Emily Watson", "recipient_role": "Recruiting Director"}
    )
    msg_id = gen_res.json()["id"]

    # Mark as sent
    sent_res = client.post(f"/api/linkedin/{msg_id}/mark-sent", headers=headers)
    assert sent_res.status_code == 200
    data = sent_res.json()
    assert data["status"] == "SENT"
    assert data["sent_at"] is not None

    # Check job status is now CONTACTED
    job_check = client.get(f"/api/jobs/{job_id}", headers=headers)
    assert job_check.status_code == 200
    assert job_check.json()["status"] == JobStatus.CONTACTED.value


def test_delete_linkedin_message(client, linkedin_job_setup):
    """Test deleting a LinkedIn message"""
    job_id = linkedin_job_setup["job_id"]
    headers = linkedin_job_setup["headers"]

    gen_res = client.post(
        f"/api/jobs/{job_id}/linkedin/generate",
        headers=headers,
        json={"recipient_name": "To Delete"}
    )
    msg_id = gen_res.json()["id"]

    del_res = client.delete(f"/api/linkedin/{msg_id}", headers=headers)
    assert del_res.status_code == 200

    # Ensure it's deleted
    get_res = client.get(f"/api/linkedin/{msg_id}", headers=headers)
    assert get_res.status_code == 404


def test_linkedin_permissions(client, linkedin_job_setup):
    """Test that unauthorized users cannot view or modify someone else's LinkedIn messages"""
    job_id = linkedin_job_setup["job_id"]
    headers = linkedin_job_setup["headers"]

    gen_res = client.post(
        f"/api/jobs/{job_id}/linkedin/generate",
        headers=headers,
        json={"recipient_name": "Owner Only"}
    )
    msg_id = gen_res.json()["id"]

    # Create a second user
    client.post(
        "/api/auth/register",
        json={"name": "Hacker", "email": "hacker@example.com", "password": "password123"}
    )
    login_res = client.post(
        "/api/auth/login",
        json={"email": "hacker@example.com", "password": "password123"}
    )
    other_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Second user shouldn't be able to generate for first user's job
    bad_gen = client.post(
        f"/api/jobs/{job_id}/linkedin/generate",
        headers=other_headers,
        json={"recipient_name": "Unauthorized"}
    )
    assert bad_gen.status_code == 404

    # Second user shouldn't be able to get first user's message
    bad_get = client.get(f"/api/linkedin/{msg_id}", headers=other_headers)
    assert bad_get.status_code == 404
