import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_register_and_login(async_client: AsyncClient):
    # Register
    reg_payload = {
        "email": "testuser@example.com",
        "password": "securepassword123",
        "full_name": "Test User",
        "phone": "+919999988888",
    }
    reg_res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    assert reg_res.json()["data"]["email"] == "testuser@example.com"

    # Login via OAuth2 form
    login_res = await async_client.post(
        "/api/v1/auth/login",
        data={"username": "testuser@example.com", "password": "securepassword123"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # Access protected /auth/me
    me_res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == "testuser@example.com"
