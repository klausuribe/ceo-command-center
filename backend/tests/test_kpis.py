"""KPI endpoint contract test — auth required, shape correct."""

from __future__ import annotations


def _login(client) -> str:
    response = client.post(
        "/api/auth/login",
        json={"username": "ceo", "password": "admin123"},
    )
    return response.json()["access_token"]


def test_kpis_all_requires_auth(client):
    response = client.get("/api/kpis/all")
    assert response.status_code == 401


def test_kpis_all_returns_seven_modules(client):
    token = _login(client)
    response = client.get(
        "/api/kpis/all",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body.keys()) == {
        "sales", "receivables", "payables",
        "inventory", "expenses", "financial", "cashflow",
    }


def test_kpis_all_rejects_bad_period(client):
    token = _login(client)
    response = client.get(
        "/api/kpis/all?period=2026-3",  # should be 2026-03
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
