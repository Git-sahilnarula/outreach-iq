import pytest
from unittest.mock import patch, AsyncMock
from app.models.job import JobStatus


@pytest.fixture
def webhook_auth_headers(client):
    client.post(
        "/api/auth/register",
        json={"name": "Webhook Tester", "email": "wh_tester@example.com", "password": "password123"}
    )
    res = client.post(
        "/api/auth/login",
        json={"email": "wh_tester@example.com", "password": "password123"}
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def webhook_user_token(client, webhook_auth_headers):
    res = client.get("/api/webhooks/token", headers=webhook_auth_headers)
    assert res.status_code == 200
    return res.json()["webhook_token"]


def test_get_and_regenerate_webhook_token(client, webhook_auth_headers):
    """Test retrieving and regenerating user's inbound webhook token"""
    res1 = client.get("/api/webhooks/token", headers=webhook_auth_headers)
    assert res1.status_code == 200
    data1 = res1.json()
    token1 = data1["webhook_token"]
    assert token1.startswith("whk_")
    assert "/api/webhooks/jobs" in data1["inbound_url"]

    # Subsequent GET returns same token
    res2 = client.get("/api/webhooks/token", headers=webhook_auth_headers)
    assert res2.json()["webhook_token"] == token1

    # Regenerate token
    res3 = client.post("/api/webhooks/token/regenerate", headers=webhook_auth_headers)
    assert res3.status_code == 200
    token2 = res3.json()["webhook_token"]
    assert token2.startswith("whk_")
    assert token2 != token1


def test_inbound_job_webhook_missing_and_invalid_token(client):
    """Test that missing or invalid webhook tokens return 401 Unauthorized"""
    payload = {
        "title": "React Frontend Dev",
        "description": "Looking for React dev to build web app",
        "client_name": "Test Client"
    }

    # Missing token
    res_missing = client.post("/api/webhooks/jobs", json=payload)
    assert res_missing.status_code == 401
    assert "Missing webhook authentication token" in res_missing.json()["detail"]

    # Invalid token header
    res_invalid = client.post("/api/webhooks/jobs", json=payload, headers={"X-Webhook-Token": "whk_invalid_token_123"})
    assert res_invalid.status_code == 401
    assert "Invalid webhook token" in res_invalid.json()["detail"]


def test_inbound_job_webhook_success_header_and_query(client, webhook_auth_headers, webhook_user_token):
    """Test successful ingestion via header and query parameter"""
    payload1 = {
        "title": "n8n Python Backend Integration Specialist",
        "description": "Build high volume API integrations using FastAPI and n8n workflows.",
        "client_name": "AutomateCorp",
        "client_email": "leads@automatecorp.com",
        "budget": "$5,000 fixed",
        "source": "upwork",
        "source_job_id": "upwork_1001"
    }

    # Header authentication
    res1 = client.post(
        "/api/webhooks/jobs",
        json=payload1,
        headers={"X-Webhook-Token": webhook_user_token}
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["success"] is True
    assert data1["is_duplicate"] is False
    job_id = data1["job_id"]
    assert job_id is not None

    # Verify job is accessible via jobs API
    get_res = client.get(f"/api/jobs/{job_id}", headers=webhook_auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == payload1["title"]
    assert get_res.json()["source"] == "upwork"

    # Query param authentication with another job
    payload2 = {
        "title": "Next.js Dashboard Engineer",
        "description": "Build analytics dashboards with Tailwind CSS and Next.js.",
        "client_name": "DataFlow Inc",
        "budget": "$80/hr"
    }
    res2 = client.post(
        f"/api/webhooks/jobs?token={webhook_user_token}",
        json=payload2
    )
    assert res2.status_code == 200
    assert res2.json()["success"] is True
    assert res2.json()["job_id"] != job_id


def test_inbound_job_webhook_duplicate_detection(client, webhook_user_token):
    """Test duplicate detection on repeated inbound webhook calls"""
    payload = {
        "title": "Senior Vue & Golang Engineer",
        "description": "Unique role for building real-time microservices and dashboards.",
        "client_name": "MicroStream",
        "source_job_id": "job_dup_999"
    }

    res1 = client.post("/api/webhooks/jobs", json=payload, headers={"X-Webhook-Token": webhook_user_token})
    assert res1.status_code == 200
    assert res1.json()["success"] is True
    assert res1.json()["is_duplicate"] is False
    first_id = res1.json()["job_id"]

    # Second call with same source_job_id and content
    res2 = client.post("/api/webhooks/jobs", json=payload, headers={"X-Webhook-Token": webhook_user_token})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["success"] is False
    assert data2["is_duplicate"] is True
    assert data2["job_id"] == first_id


def test_inbound_job_webhook_auto_analysis_high_match(client, webhook_auth_headers, webhook_user_token):
    """Test that inbound webhook automatically evaluates high match when profile exists"""
    # Create profile
    client.post(
        "/api/profile",
        headers=webhook_auth_headers,
        json={
            "startup_name": "Automation Wizards",
            "description": "We specialize in n8n, AI agents, and custom backend development.",
            "technical_skills": ["Python", "FastAPI", "n8n", "Docker"],
            "services": ["Workflow Automation", "API Development"],
            "remote_allowed": True
        }
    )

    mock_analysis = {
        "can_do": True,
        "match_score": 92,
        "technical_match": 95,
        "service_match": 90,
        "experience_match": 92,
        "budget_match": 90,
        "location_match": 95,
        "reasoning": ["Perfect match for Python & automation skills", "Budget meets targets"],
        "key_strengths": ["Deep n8n knowledge", "FastAPI mastery"],
        "missing_requirements": [],
        "risks": ["Short delivery timeline"],
        "recommended_action": "APPLY_NOW",
        "recommendation": "Strongly recommended: apply immediately with tailored proposal."
    }

    with patch("app.ai.ollama_provider.OllamaProvider.analyze_opportunity", new_callable=AsyncMock) as mock_ai:
        from app.schemas.job_analysis import JobAnalysisCreate
        mock_ai.return_value = JobAnalysisCreate(**mock_analysis)

        payload = {
            "title": "Need n8n & FastAPI Architect for Enterprise Automation",
            "description": "Looking for top-tier consultant to automate workflows using n8n and FastAPI.",
            "client_name": "Enterprise Solutions LLC",
            "budget": "$10,000 fixed"
        }

        res = client.post(
            "/api/webhooks/jobs",
            json=payload,
            headers={"X-Webhook-Token": webhook_user_token}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["match_score"] == 92.0

        # Verify job status transitioned to REVIEW_REQUIRED
        job_res = client.get(f"/api/jobs/{data['job_id']}", headers=webhook_auth_headers)
        assert job_res.status_code == 200
        assert job_res.json()["status"] == JobStatus.REVIEW_REQUIRED.value


def test_outbound_webhook_subscriptions_crud(client, webhook_auth_headers):
    """Test creating, listing, updating, and deleting outbound webhook subscriptions"""
    # 1. Create subscription
    sub_payload = {
        "target_url": "https://n8n.mycompany.com/webhook/outreach-alerts",
        "description": "Slack Alert Workflow in n8n",
        "secret_token": "super_secret_signing_key_999",
        "events": ["job.high_match", "proposal.ready"],
        "is_active": True
    }
    create_res = client.post("/api/webhooks/subscriptions", json=sub_payload, headers=webhook_auth_headers)
    assert create_res.status_code == 201
    sub = create_res.json()
    assert sub["target_url"] == sub_payload["target_url"]
    assert sub["description"] == sub_payload["description"]
    assert sub["events"] == ["job.high_match", "proposal.ready"]
    assert sub["is_active"] is True
    sub_id = sub["id"]

    # 2. List subscriptions
    list_res = client.get("/api/webhooks/subscriptions", headers=webhook_auth_headers)
    assert list_res.status_code == 200
    subs = list_res.json()
    assert len(subs) >= 1
    assert any(s["id"] == sub_id for s in subs)

    # 3. Update subscription
    update_res = client.put(
        f"/api/webhooks/subscriptions/{sub_id}",
        json={"description": "Updated Slack Alert Workflow", "is_active": False},
        headers=webhook_auth_headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["description"] == "Updated Slack Alert Workflow"
    assert update_res.json()["is_active"] is False

    # 4. Delete subscription
    del_res = client.delete(f"/api/webhooks/subscriptions/{sub_id}", headers=webhook_auth_headers)
    assert del_res.status_code == 204

    # Confirm deletion
    get_after = client.get("/api/webhooks/subscriptions", headers=webhook_auth_headers)
    assert not any(s["id"] == sub_id for s in get_after.json())


def test_test_webhook_ping(client, webhook_auth_headers):
    """Test triggering a test ping to an outbound subscription"""
    # Create subscription
    create_res = client.post(
        "/api/webhooks/subscriptions",
        json={
            "target_url": "https://webhook.site/mock-endpoint",
            "description": "Test Ping Receiver",
            "events": ["*"]
        },
        headers=webhook_auth_headers
    )
    assert create_res.status_code == 201
    sub_id = create_res.json()["id"]

    # Mock send_test_ping
    with patch("app.api.webhooks.send_test_ping", new_callable=AsyncMock) as mock_ping:
        mock_ping.return_value = (True, 200, '{"ok": true}')

        test_res = client.post(f"/api/webhooks/subscriptions/{sub_id}/test", headers=webhook_auth_headers)
        assert test_res.status_code == 200
        test_data = test_res.json()
        assert test_data["success"] is True
        assert test_data["status_code"] == 200
        assert "dispatched" in test_data["message"]
