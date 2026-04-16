"""Health endpoint tests."""

from __future__ import annotations


def test_health_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app_name"]
    assert body["version"] == "1.0.0"


def test_health_does_not_require_auth(client):
    response = client.get("/api/health")
    assert response.status_code == 200


def test_openapi_reachable(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json().get("paths", {})
    assert "/api/health" in paths
    assert "/api/auth/login" in paths
    assert "/api/kpis/all" in paths
