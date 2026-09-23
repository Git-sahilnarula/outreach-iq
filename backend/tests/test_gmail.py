"""
Tests for Phase 2 Gmail integration.

Covers:
- Gmail status endpoint (connected/disconnected)
- OAuth URL generation
- Email parsing (with mocked AI)
- Sync endpoint (with mocked Gmail client)
- Duplicate detection for Gmail-sourced jobs
- Disconnect endpoint
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.gmail_token import GmailToken
from app.services.auth import hash_password, create_access_token

from tests.conftest import engine, TestingSessionLocal, client


def create_test_user_and_token():
    """Helper: create a user in the test DB and return a JWT bearer token."""
    db = TestingSessionLocal()
    user = User(name="Test User", email="test@gmail.com", password_hash=hash_password("password123"))
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    token = create_access_token({"sub": user.email})
    return user.id, f"Bearer {token}"


# -------------------------------------------------------------------
# GET /api/gmail/status
# -------------------------------------------------------------------
class TestGmailStatus:
    def test_status_not_connected(self):
        _, auth = create_test_user_and_token()
        res = client.get("/api/gmail/status", headers={"Authorization": auth})
        assert res.status_code == 200
        data = res.json()
        assert data["connected"] is False
        assert data["gmail_email"] is None

    def test_status_connected(self):
        user_id, auth = create_test_user_and_token()
        db = TestingSessionLocal()
        token_record = GmailToken(
            user_id=user_id,
            access_token="fake_access",
            refresh_token="fake_refresh",
            gmail_email="myaccount@gmail.com",
        )
        db.add(token_record)
        db.commit()
        db.close()

        res = client.get("/api/gmail/status", headers={"Authorization": auth})
        assert res.status_code == 200
        data = res.json()
        assert data["connected"] is True
        assert data["gmail_email"] == "myaccount@gmail.com"


# -------------------------------------------------------------------
# GET /api/gmail/auth-url
# -------------------------------------------------------------------
class TestGmailAuthUrl:
    def test_auth_url_not_configured(self):
        """Should return 503 when GOOGLE_CLIENT_ID is not set."""
        _, auth = create_test_user_and_token()
        with patch("app.api.gmail._gmail_configured", return_value=False):
            res = client.get("/api/gmail/auth-url", headers={"Authorization": auth})
        assert res.status_code == 503

    def test_auth_url_configured(self):
        """Should return an auth URL when credentials are configured."""
        _, auth = create_test_user_and_token()
        with patch("app.api.gmail._gmail_configured", return_value=True), \
             patch("app.integrations.gmail_client.get_auth_url", return_value="https://accounts.google.com/o/oauth2/auth?..."):
            res = client.get("/api/gmail/auth-url", headers={"Authorization": auth})
        assert res.status_code == 200
        assert "auth_url" in res.json()
        assert res.json()["auth_url"].startswith("https://")


# -------------------------------------------------------------------
# DELETE /api/gmail/disconnect
# -------------------------------------------------------------------
class TestGmailDisconnect:
    def test_disconnect_no_connection(self):
        _, auth = create_test_user_and_token()
        res = client.delete("/api/gmail/disconnect", headers={"Authorization": auth})
        assert res.status_code == 404

    def test_disconnect_success(self):
        user_id, auth = create_test_user_and_token()
        db = TestingSessionLocal()
        db.add(GmailToken(user_id=user_id, access_token="tok", refresh_token="ref", gmail_email="x@gmail.com"))
        db.commit()
        db.close()

        res = client.delete("/api/gmail/disconnect", headers={"Authorization": auth})
        assert res.status_code == 200
        assert "disconnected" in res.json()["message"].lower()

        # Verify removed from DB
        db = TestingSessionLocal()
        record = db.query(GmailToken).filter(GmailToken.user_id == user_id).first()
        db.close()
        assert record is None


# -------------------------------------------------------------------
# POST /api/gmail/sync
# -------------------------------------------------------------------
class TestGmailSync:
    def test_sync_not_connected(self):
        _, auth = create_test_user_and_token()
        with patch("app.api.gmail._gmail_configured", return_value=True):
            res = client.post("/api/gmail/sync", headers={"Authorization": auth})
        assert res.status_code == 400
        assert "not connected" in res.json()["detail"].lower()

    def test_sync_not_configured(self):
        _, auth = create_test_user_and_token()
        with patch("app.api.gmail._gmail_configured", return_value=False):
            res = client.post("/api/gmail/sync", headers={"Authorization": auth})
        assert res.status_code == 503

    def test_sync_no_emails(self):
        user_id, auth = create_test_user_and_token()
        db = TestingSessionLocal()
        db.add(GmailToken(user_id=user_id, access_token="tok", refresh_token="ref"))
        db.commit()
        db.close()

        with patch("app.api.gmail._gmail_configured", return_value=True), \
             patch("app.integrations.gmail_client.is_connected", return_value=True), \
             patch("app.integrations.gmail_client.fetch_job_alert_emails", return_value=[]), \
             patch("app.integrations.gmail_client.mark_as_processed"), \
             patch("app.integrations.gmail_client.update_last_sync"):
            res = client.post("/api/gmail/sync", headers={"Authorization": auth})

        assert res.status_code == 200
        data = res.json()
        assert data["new_jobs"] == 0
        assert data["total_processed"] == 0

    def test_sync_creates_new_job(self):
        user_id, auth = create_test_user_and_token()
        db = TestingSessionLocal()
        db.add(GmailToken(user_id=user_id, access_token="tok", refresh_token="ref"))
        db.commit()
        db.close()

        fake_email = {
            "id": "msg_abc123",
            "thread_id": "thread_abc",
            "subject": "Senior Python Developer at Acme",
            "sender": "alerts@linkedin.com",
            "date": "Mon, 22 Sep 2026",
            "body_text": "Job: Senior Python Developer\nCompany: Acme Corp\nLocation: Remote\nSalary: $120k-$160k",
            "snippet": "Senior Python Developer...",
        }

        from app.schemas.job import JobCreate
        fake_job_create = JobCreate(
            source="gmail",
            source_job_id="msg_abc123",
            title="Senior Python Developer",
            company="Acme Corp",
            description="We are looking for a senior Python developer.",
            location="Remote",
            job_type="full-time",
        )

        with patch("app.api.gmail._gmail_configured", return_value=True), \
             patch("app.integrations.gmail_client.is_connected", return_value=True), \
             patch("app.integrations.gmail_client.fetch_job_alert_emails", return_value=[fake_email]), \
             patch("app.integrations.email_parser.parse_job_from_email", new_callable=AsyncMock, return_value=fake_job_create), \
             patch("app.integrations.gmail_client.mark_as_processed"), \
             patch("app.integrations.gmail_client.update_last_sync"):
            res = client.post("/api/gmail/sync", headers={"Authorization": auth})

        assert res.status_code == 200
        data = res.json()
        assert data["new_jobs"] == 1
        assert data["duplicates_skipped"] == 0

    def test_sync_skips_duplicates(self):
        """Second sync of same message_id should be caught by duplicate detection."""
        user_id, auth = create_test_user_and_token()
        db = TestingSessionLocal()
        db.add(GmailToken(user_id=user_id, access_token="tok", refresh_token="ref"))
        db.commit()
        db.close()

        fake_email = {
            "id": "msg_dup999",
            "thread_id": "thread_dup",
            "subject": "Python Job",
            "sender": "alerts@indeed.com",
            "date": "Mon, 22 Sep 2026",
            "body_text": "Python developer needed",
            "snippet": "Python...",
        }

        from app.schemas.job import JobCreate
        fake_job_create = JobCreate(
            source="gmail",
            source_job_id="msg_dup999",
            title="Python Job",
            company="Duplicate Corp",
            description="Python developer needed at Duplicate Corp.",
        )

        with patch("app.api.gmail._gmail_configured", return_value=True), \
             patch("app.integrations.gmail_client.is_connected", return_value=True), \
             patch("app.integrations.gmail_client.fetch_job_alert_emails", return_value=[fake_email]), \
             patch("app.integrations.email_parser.parse_job_from_email", new_callable=AsyncMock, return_value=fake_job_create), \
             patch("app.integrations.gmail_client.mark_as_processed"), \
             patch("app.integrations.gmail_client.update_last_sync"):
            # First sync
            client.post("/api/gmail/sync", headers={"Authorization": auth})
            # Second sync — same email
            res = client.post("/api/gmail/sync", headers={"Authorization": auth})

        assert res.status_code == 200
        data = res.json()
        assert data["new_jobs"] == 0
        assert data["duplicates_skipped"] == 1

    def test_sync_skips_non_job_email(self):
        user_id, auth = create_test_user_and_token()
        db = TestingSessionLocal()
        db.add(GmailToken(user_id=user_id, access_token="tok", refresh_token="ref"))
        db.commit()
        db.close()

        fake_email = {
            "id": "msg_promo",
            "thread_id": "thread_promo",
            "subject": "Flash sale 50% off everything!",
            "sender": "promo@shop.com",
            "date": "Mon, 22 Sep 2026",
            "body_text": "Big sale happening now!",
            "snippet": "Sale...",
        }

        with patch("app.api.gmail._gmail_configured", return_value=True), \
             patch("app.integrations.gmail_client.is_connected", return_value=True), \
             patch("app.integrations.gmail_client.fetch_job_alert_emails", return_value=[fake_email]), \
             patch("app.integrations.email_parser.parse_job_from_email", new_callable=AsyncMock, return_value=None), \
             patch("app.integrations.gmail_client.mark_as_processed"), \
             patch("app.integrations.gmail_client.update_last_sync"):
            res = client.post("/api/gmail/sync", headers={"Authorization": auth})

        assert res.status_code == 200
        data = res.json()
        assert data["new_jobs"] == 0
        assert data["not_job_emails"] == 1


# -------------------------------------------------------------------
# Email parser unit tests
# -------------------------------------------------------------------
class TestEmailParser:
    def test_html_to_text(self):
        from app.integrations.email_parser import html_to_text
        html = "<h1>Job Title</h1><p>We are hiring a <strong>Python developer</strong>.</p>"
        result = html_to_text(html)
        assert "Python developer" in result
        assert "<" not in result  # HTML stripped

    def test_clean_email_body_truncates(self):
        from app.integrations.email_parser import clean_email_body
        long_body = "word " * 1000  # > 4000 chars
        result = clean_email_body(long_body)
        assert len(result) <= 4100  # Approximately truncated
        assert "truncated" in result

    def test_extract_domain(self):
        from app.integrations.email_parser import _extract_domain
        assert _extract_domain("Jobs Alert <alerts@linkedin.com>") == "Linkedin"
        assert _extract_domain("no-reply@gmail.com") is None  # Common provider skipped
        assert _extract_domain("noreply@acmecorp.com") == "Acmecorp"

    @pytest.mark.asyncio
    async def test_parse_job_from_email_with_mocked_ai(self):
        from app.integrations.email_parser import parse_job_from_email

        ai_response = json.dumps({
            "is_job_opportunity": True,
            "title": "Backend Engineer",
            "company": "TechCo",
            "description": "We need a backend engineer with Python experience.",
            "url": "https://techco.com/jobs/123",
            "location": "Remote",
            "job_type": "full-time",
            "salary_min": 90000,
            "salary_max": 130000,
            "currency": "USD",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
        })

        with patch("app.integrations.email_parser.get_ai_provider") as mock_provider_fn:
            mock_provider = MagicMock()
            mock_provider._call_ollama = AsyncMock(return_value=ai_response)
            mock_provider_fn.return_value = mock_provider

            result = await parse_job_from_email(
                subject="New Job: Backend Engineer at TechCo",
                sender="alerts@linkedin.com",
                body="Backend Engineer opening at TechCo. Remote. $90k-$130k.",
                message_id="msg_test_001",
            )

        assert result is not None
        assert result.title == "Backend Engineer"
        assert result.company == "TechCo"
        assert result.source == "gmail"
        assert result.source_job_id == "msg_test_001"
        assert result.salary_min == 90000.0

    @pytest.mark.asyncio
    async def test_parse_non_job_email_returns_none(self):
        from app.integrations.email_parser import parse_job_from_email

        ai_response = json.dumps({
            "is_job_opportunity": False,
            "title": None,
            "company": None,
            "description": None,
            "url": None,
            "location": None,
            "job_type": None,
            "salary_min": None,
            "salary_max": None,
            "currency": "USD",
            "skills": [],
        })

        with patch("app.integrations.email_parser.get_ai_provider") as mock_provider_fn:
            mock_provider = MagicMock()
            mock_provider._call_ollama = AsyncMock(return_value=ai_response)
            mock_provider_fn.return_value = mock_provider

            result = await parse_job_from_email(
                subject="Big sale happening now!",
                sender="promo@shop.com",
                body="50% off everything this weekend.",
                message_id="msg_promo_001",
            )

        assert result is None
