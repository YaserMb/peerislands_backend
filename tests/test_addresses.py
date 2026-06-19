from fastapi.testclient import TestClient


def _register_and_login(
    client: TestClient,
    *,
    email: str = "yaser@example.com",
) -> dict[str, str]:
    password = "secure-password"
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Yaser Basravi",
            "email": email,
            "password": password,
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _address_payload(**overrides) -> dict:
    payload = {
        "full_name": "Yaser Basravi",
        "phone": "8668590057",
        "address_line1": "Flat 101, Example Apartments",
        "address_line2": "Baner",
        "city": "Pune",
        "state": "Maharashtra",
        "postal_code": "411045",
        "country": "India",
        "is_default": False,
    }
    payload.update(overrides)
    return payload


def test_create_list_retrieve_update_and_delete_address(client: TestClient) -> None:
    headers = _register_and_login(client)

    create_response = client.post(
        "/api/v1/addresses",
        json=_address_payload(),
        headers=headers,
    )

    assert create_response.status_code == 201
    created_address = create_response.json()
    assert created_address["full_name"] == "Yaser Basravi"
    assert created_address["is_default"] is True

    list_response = client.get("/api/v1/addresses", headers=headers)
    assert list_response.status_code == 200
    assert [address["id"] for address in list_response.json()] == [created_address["id"]]

    retrieve_response = client.get(
        f"/api/v1/addresses/{created_address['id']}",
        headers=headers,
    )
    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["id"] == created_address["id"]

    update_response = client.patch(
        f"/api/v1/addresses/{created_address['id']}",
        json={"city": "Mumbai", "address_line2": None},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["city"] == "Mumbai"
    assert update_response.json()["address_line2"] is None

    delete_response = client.delete(
        f"/api/v1/addresses/{created_address['id']}",
        headers=headers,
    )
    assert delete_response.status_code == 204

    list_after_delete_response = client.get("/api/v1/addresses", headers=headers)
    assert list_after_delete_response.status_code == 200
    assert list_after_delete_response.json() == []


def test_setting_default_address_clears_previous_default(client: TestClient) -> None:
    headers = _register_and_login(client)

    first_response = client.post(
        "/api/v1/addresses",
        json=_address_payload(address_line1="First address"),
        headers=headers,
    )
    second_response = client.post(
        "/api/v1/addresses",
        json=_address_payload(address_line1="Second address", is_default=True),
        headers=headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    first_id = first_response.json()["id"]
    second_id = second_response.json()["id"]

    list_response = client.get("/api/v1/addresses", headers=headers)
    addresses_by_id = {
        address["id"]: address
        for address in list_response.json()
    }

    assert addresses_by_id[first_id]["is_default"] is False
    assert addresses_by_id[second_id]["is_default"] is True

    update_response = client.patch(
        f"/api/v1/addresses/{first_id}",
        json={"is_default": True},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["is_default"] is True

    list_response = client.get("/api/v1/addresses", headers=headers)
    addresses_by_id = {
        address["id"]: address
        for address in list_response.json()
    }
    assert addresses_by_id[first_id]["is_default"] is True
    assert addresses_by_id[second_id]["is_default"] is False


def test_address_endpoints_require_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/addresses")

    assert response.status_code == 401


def test_address_ownership_is_enforced(client: TestClient) -> None:
    owner_headers = _register_and_login(client, email="owner@example.com")
    other_headers = _register_and_login(client, email="other@example.com")
    create_response = client.post(
        "/api/v1/addresses",
        json=_address_payload(),
        headers=owner_headers,
    )
    address_id = create_response.json()["id"]

    retrieve_response = client.get(
        f"/api/v1/addresses/{address_id}",
        headers=other_headers,
    )
    update_response = client.patch(
        f"/api/v1/addresses/{address_id}",
        json={"city": "Mumbai"},
        headers=other_headers,
    )
    delete_response = client.delete(
        f"/api/v1/addresses/{address_id}",
        headers=other_headers,
    )

    assert retrieve_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404

    owner_list_response = client.get("/api/v1/addresses", headers=owner_headers)
    other_list_response = client.get("/api/v1/addresses", headers=other_headers)

    assert [address["id"] for address in owner_list_response.json()] == [address_id]
    assert other_list_response.json() == []
