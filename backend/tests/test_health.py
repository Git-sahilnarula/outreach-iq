def test_health_check_endpoint(client):
    """Test the upgraded system health check endpoint"""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["service"] == "outreach-iq-api"
    assert data["version"] == "1.0.0"
    assert "checks" in data
    assert data["checks"]["database"] == "connected"
    assert "timestamp" in data
