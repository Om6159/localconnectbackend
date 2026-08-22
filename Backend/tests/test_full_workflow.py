import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_need_match_connect_workflow(async_client: AsyncClient):
    # 1. Register Requester
    req_user = {
        "email": "aarav.requester@example.com",
        "password": "password123",
        "full_name": "Aarav Requester",
    }
    r1 = await async_client.post("/api/v1/auth/register", json=req_user)
    assert r1.status_code == 201

    # Login Requester
    l1 = await async_client.post(
        "/api/v1/auth/login",
        data={"username": "aarav.requester@example.com", "password": "password123"},
    )
    req_token = l1.json()["access_token"]
    req_headers = {"Authorization": f"Bearer {req_token}"}

    # 2. Register Provider User
    prov_user = {
        "email": "ramesh.tutor@example.com",
        "password": "password123",
        "full_name": "Ramesh Tutor",
    }
    r2 = await async_client.post("/api/v1/auth/register", json=prov_user)
    assert r2.status_code == 201

    # Login Provider User
    l2 = await async_client.post(
        "/api/v1/auth/login",
        data={"username": "ramesh.tutor@example.com", "password": "password123"},
    )
    prov_token = l2.json()["access_token"]
    prov_headers = {"Authorization": f"Bearer {prov_token}"}

    # Create Provider Profile
    prov_profile_payload = {
        "display_name": "Ramesh Maths Academy",
        "bio": "Specialist in Class 10 & 12 Maths",
        "experience_years": 7,
        "service_radius_km": 10.0,
        "location": {
            "city": "Mumbai",
            "locality": "Andheri",
            "latitude": 19.1197,
            "longitude": 72.8464,
        },
    }
    p_res = await async_client.post("/api/v1/providers", json=prov_profile_payload, headers=prov_headers)
    assert p_res.status_code == 201
    provider_id = p_res.json()["data"]["id"]

    # 3. Create Request ("NEED")
    req_payload = {
        "raw_description": "I need a Class 10 maths tutor near me on weekends under ₹500",
        "budget_max": 500.0,
        "radius_km": 10.0,
        "latitude": 19.0760,
        "longitude": 72.8777,
    }
    create_req_res = await async_client.post("/api/v1/requests", json=req_payload, headers=req_headers)
    assert create_req_res.status_code == 201
    request_id = create_req_res.json()["data"]["id"]
    assert create_req_res.json()["data"]["ai_parsed_requirement"]["category"] == "Education"

    # 4. Run Matching Engine ("MATCH")
    match_res = await async_client.post(f"/api/v1/requests/{request_id}/match", headers=req_headers)
    assert match_res.status_code == 200
    matches = match_res.json()["data"]
    assert len(matches) > 0
    match_id = matches[0]["id"]
    assert matches[0]["provider_id"] == provider_id

    # 5. Connect ("CONNECT")
    conn_payload = {
        "request_id": request_id,
        "provider_id": provider_id,
        "match_id": match_id,
    }
    conn_res = await async_client.post("/api/v1/connections", json=conn_payload, headers=req_headers)
    assert conn_res.status_code == 200
    connection_id = conn_res.json()["data"]["id"]

    # 6. Provider Accepts Connection
    accept_res = await async_client.post(f"/api/v1/connections/{connection_id}/accept", headers=prov_headers)
    assert accept_res.status_code == 200
    assert accept_res.json()["data"]["status"] == "active"

    # 7. Complete Connection (Dual Confirmation)
    c1 = await async_client.post(f"/api/v1/connections/{connection_id}/complete", headers=req_headers)
    assert c1.status_code == 200

    c2 = await async_client.post(f"/api/v1/connections/{connection_id}/complete", headers=prov_headers)
    assert c2.status_code == 200
    assert c2.json()["data"]["status"] == "completed"

    # 8. Submit Review
    rev_payload = {
        "rating": 5,
        "review_text": "Excellent math tutor, clear explanations!",
    }
    rev_res = await async_client.post(f"/api/v1/connections/{connection_id}/review", json=rev_payload, headers=req_headers)
    assert rev_res.status_code == 201
    assert rev_res.json()["data"]["rating"] == 5

    # 9. Verify Provider Trust Score
    trust_res = await async_client.get(f"/api/v1/providers/{provider_id}/trust")
    assert trust_res.status_code == 200
    assert trust_res.json()["data"]["trust_score"] > 0
