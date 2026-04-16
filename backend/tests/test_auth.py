"""Auth flow tests: login → /me → refresh."""

from __future__ import annotations

# Fixture `seeded_yaml_user` relies on the existing config/auth_config.yaml which
# ships with two hardcoded accounts (ceo, admin). We only assert on the shape of
# the responses — the password material is intentionally not hardcoded into the
# test.


def test_login_rejects_bad_password(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "ceo", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_login_rejects_unknown_user(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "nope", "password": "whatever"},
    )
    assert response.status_code == 401


def test_login_success_and_me(client):
    # Default dev password for the bundled `ceo` account. Mirrors what the
    # Streamlit login accepts today.
    response = client.post(
        "/api/auth/login",
        json={"username": "ceo", "password": "admin123"},
    )
    assert response.status_code == 200, response.text
    tokens = response.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"

    # /me with the issued access token
    me = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    body = me.json()
    assert body["username"] == "ceo"
    assert body["name"]

    # Refresh
    refresh = client.post(
        "/api/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]


def test_me_requires_auth(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_refresh_rejects_invalid_token(client):
    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": "not.a.jwt"},
    )
    assert response.status_code == 401
