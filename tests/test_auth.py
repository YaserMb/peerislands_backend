from fastapi.testclient import TestClient


def test_register_login_and_read_current_user(client: TestClient) -> None:
    payload = {
        "name": "Yaser Basravi",
        "email": "yaser@example.com",
        "password": "secure-password",
    }

    register_response = client.post("/api/v1/auth/register", json=payload)

    assert register_response.status_code == 201
    registered_user = register_response.json()
    assert registered_user["email"] == payload["email"]
    assert registered_user["role"] == "CUSTOMER"
    assert "password" not in registered_user
    assert "hashed_password" not in registered_user

    duplicate_response = client.post("/api/v1/auth/register", json=payload)
    assert duplicate_response.status_code == 409

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": payload["email"], "password": payload["password"]},
    )

    assert login_response.status_code == 200
    token_payload = login_response.json()
    assert token_payload["token_type"] == "bearer"
    assert token_payload["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_payload['access_token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == payload["email"]


def test_login_rejects_bad_password(client: TestClient) -> None:
    payload = {
        "name": "Yaser Basravi",
        "email": "yaser@example.com",
        "password": "secure-password",
    }
    client.post("/api/v1/auth/register", json=payload)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": payload["email"], "password": "wrong-password"},
    )

    assert response.status_code == 401
