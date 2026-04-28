"""Tests for registration and login."""

from sqlalchemy import select

from app.models import User


async def test_register_creates_user(async_client, db_session):
    response = await async_client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert "password" not in body

    user = await db_session.scalar(select(User).where(User.email == "alice@example.com"))
    assert user is not None
    assert user.password_hash != "password123"


async def test_register_duplicate_email_409(async_client):
    payload = {"email": "dup@example.com", "password": "password123"}
    await async_client.post("/auth/register", json=payload)
    response = await async_client.post("/auth/register", json=payload)
    assert response.status_code == 409


async def test_register_case_insensitive_duplicate(async_client):
    await async_client.post(
        "/auth/register",
        json={"email": "case@example.com", "password": "password123"},
    )
    response = await async_client.post(
        "/auth/register",
        json={"email": "CASE@EXAMPLE.COM", "password": "password123"},
    )
    assert response.status_code == 409


async def test_register_invalid_email_422(async_client):
    response = await async_client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "password123"},
    )
    assert response.status_code == 422


async def test_register_short_password_422(async_client):
    response = await async_client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "short"},
    )
    assert response.status_code == 422


async def test_login_returns_token(async_client):
    payload = {"email": "bob@example.com", "password": "password123"}
    await async_client.post("/auth/register", json=payload)
    response = await async_client.post("/auth/login", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


async def test_login_wrong_password_401(async_client):
    await async_client.post(
        "/auth/register",
        json={"email": "wrong@example.com", "password": "password123"},
    )
    response = await async_client.post(
        "/auth/login",
        json={"email": "wrong@example.com", "password": "badpassword"},
    )
    assert response.status_code == 401


async def test_login_unknown_email_401(async_client):
    response = await async_client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert response.status_code == 401


async def test_login_accepts_json_not_form(async_client):
    await async_client.post(
        "/auth/register",
        json={"email": "form@example.com", "password": "password123"},
    )
    response = await async_client.post(
        "/auth/login",
        data={"username": "form@example.com", "password": "password123"},
    )
    assert response.status_code == 422
