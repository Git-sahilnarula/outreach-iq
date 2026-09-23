"""
Tests for Phase 3 — Notifications & Approval Workflow.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.job import Job, JobStatus
from app.models.notification import Notification, NotificationType
from app.services.auth import hash_password, create_access_token
from app.services import notification_service

from tests.conftest import engine, TestingSessionLocal, client


def make_user_and_token(email="test@example.com"):
    db = TestingSessionLocal()
    user = User(name="Test", email=email, password_hash=hash_password("pass"))
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    token = create_access_token({"sub": user.email})
    return user.id, f"Bearer {token}"


def make_job(user_id: int, title="Test Job", company="Acme", status=JobStatus.NEW) -> int:
    db = TestingSessionLocal()
    job = Job(
        user_id=user_id,
        source="manual",
        title=title,
        company=company,
        description="Sample job description.",
        status=status,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    job_id = job.id
    db.close()
    return job_id


# ---------------------------------------------------------------------------
# Notification service unit tests
# ---------------------------------------------------------------------------

class TestNotificationService:
    def test_create_notification(self):
        user_id, _ = make_user_and_token("svc@test.com")
        db = TestingSessionLocal()
        notif = notification_service.create_notification(
            db, user_id, NotificationType.NEW_JOB,
            title="New Job", message="A job was added.",
        )
        assert notif.id is not None
        assert notif.read is False
        assert notif.type == NotificationType.NEW_JOB.value
        db.close()

    def test_unread_count_increments(self):
        user_id, _ = make_user_and_token("cnt@test.com")
        db = TestingSessionLocal()
        assert notification_service.get_unread_count(db, user_id) == 0
        notification_service.create_notification(db, user_id, NotificationType.NEW_JOB, "A", "B")
        notification_service.create_notification(db, user_id, NotificationType.REVIEW_REQUIRED, "C", "D")
        assert notification_service.get_unread_count(db, user_id) == 2
        db.close()

    def test_mark_read_decrements_count(self):
        user_id, _ = make_user_and_token("mr@test.com")
        db = TestingSessionLocal()
        n = notification_service.create_notification(db, user_id, NotificationType.NEW_JOB, "T", "M")
        notification_service.mark_read(db, user_id, n.id)
        assert notification_service.get_unread_count(db, user_id) == 0
        db.close()

    def test_mark_all_read(self):
        user_id, _ = make_user_and_token("mar@test.com")
        db = TestingSessionLocal()
        for i in range(3):
            notification_service.create_notification(db, user_id, NotificationType.NEW_JOB, f"T{i}", "M")
        updated = notification_service.mark_all_read(db, user_id)
        assert updated == 3
        assert notification_service.get_unread_count(db, user_id) == 0
        db.close()

    def test_clear_all(self):
        user_id, _ = make_user_and_token("ca@test.com")
        db = TestingSessionLocal()
        for i in range(5):
            notification_service.create_notification(db, user_id, NotificationType.NEW_JOB, f"T{i}", "M")
        deleted = notification_service.clear_all(db, user_id)
        assert deleted == 5
        assert notification_service.get_unread_count(db, user_id) == 0
        db.close()

    def test_get_notifications_ordered_newest_first(self):
        user_id, _ = make_user_and_token("order@test.com")
        db = TestingSessionLocal()
        n1 = notification_service.create_notification(db, user_id, NotificationType.NEW_JOB, "First", "M")
        n2 = notification_service.create_notification(db, user_id, NotificationType.REVIEW_REQUIRED, "Second", "M")
        results = notification_service.get_notifications(db, user_id)
        assert results[0].id == n2.id  # newest first
        assert results[1].id == n1.id
        db.close()


# ---------------------------------------------------------------------------
# GET /api/notifications/count
# ---------------------------------------------------------------------------

class TestNotificationCountEndpoint:
    def test_count_zero_initially(self):
        _, auth = make_user_and_token("cnt_ep@test.com")
        res = client.get("/api/notifications/count", headers={"Authorization": auth})
        assert res.status_code == 200
        assert res.json()["unread"] == 0

    def test_count_increments_after_notification(self):
        user_id, auth = make_user_and_token("cnt_ep2@test.com")
        db = TestingSessionLocal()
        notification_service.create_notification(db, user_id, NotificationType.NEW_JOB, "T", "M")
        db.close()
        res = client.get("/api/notifications/count", headers={"Authorization": auth})
        assert res.json()["unread"] == 1

    def test_unauthenticated_count_returns_401(self):
        res = client.get("/api/notifications/count")
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/notifications/
# ---------------------------------------------------------------------------

class TestNotificationListEndpoint:
    def test_list_empty(self):
        _, auth = make_user_and_token("list@test.com")
        res = client.get("/api/notifications/", headers={"Authorization": auth})
        assert res.status_code == 200
        data = res.json()
        assert data["notifications"] == []
        assert data["unread"] == 0

    def test_list_contains_created_notifications(self):
        user_id, auth = make_user_and_token("list2@test.com")
        db = TestingSessionLocal()
        notification_service.create_notification(db, user_id, NotificationType.NEW_JOB, "T1", "M1")
        notification_service.create_notification(db, user_id, NotificationType.REVIEW_REQUIRED, "T2", "M2")
        db.close()
        res = client.get("/api/notifications/", headers={"Authorization": auth})
        assert len(res.json()["notifications"]) == 2
        assert res.json()["unread"] == 2

    def test_list_only_own_notifications(self):
        user_id1, auth1 = make_user_and_token("own1@test.com")
        user_id2, _ = make_user_and_token("own2@test.com")
        db = TestingSessionLocal()
        notification_service.create_notification(db, user_id2, NotificationType.NEW_JOB, "Other user's notif", "M")
        db.close()
        res = client.get("/api/notifications/", headers={"Authorization": auth1})
        assert res.json()["notifications"] == []


# ---------------------------------------------------------------------------
# PATCH /api/notifications/read-all
# ---------------------------------------------------------------------------

class TestMarkAllRead:
    def test_mark_all_read(self):
        user_id, auth = make_user_and_token("rall@test.com")
        db = TestingSessionLocal()
        for _ in range(3):
            notification_service.create_notification(db, user_id, NotificationType.NEW_JOB, "T", "M")
        db.close()
        res = client.patch("/api/notifications/read-all", headers={"Authorization": auth})
        assert res.status_code == 200
        assert res.json()["updated"] == 3
        # Count should now be 0
        count_res = client.get("/api/notifications/count", headers={"Authorization": auth})
        assert count_res.json()["unread"] == 0


# ---------------------------------------------------------------------------
# DELETE /api/notifications/all
# ---------------------------------------------------------------------------

class TestClearAll:
    def test_clear_all(self):
        user_id, auth = make_user_and_token("clr@test.com")
        db = TestingSessionLocal()
        for _ in range(4):
            notification_service.create_notification(db, user_id, NotificationType.NEW_JOB, "T", "M")
        db.close()
        res = client.delete("/api/notifications/all", headers={"Authorization": auth})
        assert res.status_code == 200
        assert res.json()["deleted"] == 4
        list_res = client.get("/api/notifications/", headers={"Authorization": auth})
        assert list_res.json()["notifications"] == []


# ---------------------------------------------------------------------------
# POST /api/jobs/{id}/approve
# ---------------------------------------------------------------------------

class TestApproveJob:
    def test_approve_changes_status(self):
        user_id, auth = make_user_and_token("appr@test.com")
        job_id = make_job(user_id, status=JobStatus.REVIEW_REQUIRED)
        res = client.post(f"/api/jobs/{job_id}/approve", headers={"Authorization": auth})
        assert res.status_code == 200
        assert res.json()["status"] == "APPROVED"

    def test_approve_creates_notification(self):
        user_id, auth = make_user_and_token("appr2@test.com")
        job_id = make_job(user_id, status=JobStatus.REVIEW_REQUIRED)
        client.post(f"/api/jobs/{job_id}/approve", headers={"Authorization": auth})
        db = TestingSessionLocal()
        notifs = notification_service.get_notifications(db, user_id)
        db.close()
        types = [n.type for n in notifs]
        assert NotificationType.JOB_APPROVED.value in types

    def test_approve_already_approved_returns_400(self):
        user_id, auth = make_user_and_token("appr3@test.com")
        job_id = make_job(user_id, status=JobStatus.APPROVED)
        res = client.post(f"/api/jobs/{job_id}/approve", headers={"Authorization": auth})
        assert res.status_code == 400

    def test_approve_wrong_user_returns_404(self):
        user_id1, _ = make_user_and_token("appr4a@test.com")
        _, auth2 = make_user_and_token("appr4b@test.com")
        job_id = make_job(user_id1)
        res = client.post(f"/api/jobs/{job_id}/approve", headers={"Authorization": auth2})
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/jobs/{id}/reject
# ---------------------------------------------------------------------------

class TestRejectJob:
    def test_reject_changes_status(self):
        user_id, auth = make_user_and_token("rej@test.com")
        job_id = make_job(user_id, status=JobStatus.REVIEW_REQUIRED)
        res = client.post(f"/api/jobs/{job_id}/reject", headers={"Authorization": auth})
        assert res.status_code == 200
        assert res.json()["status"] == "REJECTED"

    def test_reject_creates_notification(self):
        user_id, auth = make_user_and_token("rej2@test.com")
        job_id = make_job(user_id, status=JobStatus.NEW)
        client.post(f"/api/jobs/{job_id}/reject", headers={"Authorization": auth})
        db = TestingSessionLocal()
        notifs = notification_service.get_notifications(db, user_id)
        db.close()
        types = [n.type for n in notifs]
        assert NotificationType.JOB_REJECTED.value in types

    def test_reject_already_rejected_returns_400(self):
        user_id, auth = make_user_and_token("rej3@test.com")
        job_id = make_job(user_id, status=JobStatus.REJECTED)
        res = client.post(f"/api/jobs/{job_id}/reject", headers={"Authorization": auth})
        assert res.status_code == 400

    def test_can_re_approve_after_reject(self):
        """Approve → Reject → Approve should work (status transitions are flexible)."""
        user_id, auth = make_user_and_token("retrans@test.com")
        job_id = make_job(user_id, status=JobStatus.REVIEW_REQUIRED)
        client.post(f"/api/jobs/{job_id}/approve", headers={"Authorization": auth})
        client.post(f"/api/jobs/{job_id}/reject", headers={"Authorization": auth})
        res = client.post(f"/api/jobs/{job_id}/approve", headers={"Authorization": auth})
        assert res.status_code == 200
        assert res.json()["status"] == "APPROVED"


# ---------------------------------------------------------------------------
# Notification created when job is created via POST /api/jobs/
# ---------------------------------------------------------------------------

class TestJobCreationNotification:
    def test_new_job_creates_notification(self):
        user_id, auth = make_user_and_token("jcn@test.com")
        job_data = {
            "title": "Python Dev",
            "company": "TechCo",
            "description": "A backend role.",
            "source": "manual",
        }
        client.post("/api/jobs/", json=job_data, headers={"Authorization": auth})
        count_res = client.get("/api/notifications/count", headers={"Authorization": auth})
        assert count_res.json()["unread"] >= 1
