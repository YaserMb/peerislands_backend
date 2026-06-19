from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.orders import Order, OrderStatus
from app.db.models.products import Product
from app.db.models.users import UserRole
from app.services.products import seed_sample_products
from app.services.users import get_user_by_email


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
        "is_default": True,
    }
    payload.update(overrides)
    return payload


def _create_address(client: TestClient, headers: dict[str, str], **overrides) -> dict:
    response = client.post(
        "/api/v1/addresses",
        json=_address_payload(**overrides),
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def _create_order(
    client: TestClient,
    headers: dict[str, str],
    *,
    address_id: int,
    product_id: int,
) -> dict:
    response = client.post(
        "/api/v1/orders",
        json={
            "shipping_address_id": address_id,
            "items": [{"product_id": product_id, "quantity": 1}],
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def _promote_to_admin(db_session: Session, email: str) -> None:
    user = get_user_by_email(db_session, email)
    assert user is not None
    user.role = UserRole.ADMIN
    db_session.commit()


def test_create_order_with_multiple_items_calculates_totals_and_snapshots(
    client: TestClient,
    db_session: Session,
) -> None:
    products = seed_sample_products(db_session)
    headers = _register_and_login(client)
    address = _create_address(client, headers)

    response = client.post(
        "/api/v1/orders",
        json={
            "shipping_address_id": address["id"],
            "items": [
                {"product_id": products[0].id, "quantity": 2},
                {"product_id": products[1].id, "quantity": 1},
            ],
        },
        headers=headers,
    )

    assert response.status_code == 201
    order = response.json()
    assert order["status"] == "PENDING"
    assert order["total_amount"] == "189.97"
    assert order["shipping_full_name"] == address["full_name"]
    assert order["shipping_address_line1"] == address["address_line1"]
    assert order["items"] == [
        {
            "id": order["items"][0]["id"],
            "product_id": products[0].id,
            "product_name": "Mechanical Keyboard",
            "quantity": 2,
            "unit_price": "79.99",
            "line_total": "159.98",
        },
        {
            "id": order["items"][1]["id"],
            "product_id": products[1].id,
            "product_name": "Wireless Mouse",
            "quantity": 1,
            "unit_price": "29.99",
            "line_total": "29.99",
        },
    ]


def test_order_creation_rejects_missing_auth_empty_items_and_invalid_ownership(
    client: TestClient,
    db_session: Session,
) -> None:
    product = seed_sample_products(db_session)[0]
    owner_headers = _register_and_login(client, email="owner@example.com")
    other_headers = _register_and_login(client, email="other@example.com")
    owner_address = _create_address(client, owner_headers)

    unauthenticated_response = client.post(
        "/api/v1/orders",
        json={
            "shipping_address_id": owner_address["id"],
            "items": [{"product_id": product.id, "quantity": 1}],
        },
    )
    empty_items_response = client.post(
        "/api/v1/orders",
        json={"shipping_address_id": owner_address["id"], "items": []},
        headers=owner_headers,
    )
    other_user_address_response = client.post(
        "/api/v1/orders",
        json={
            "shipping_address_id": owner_address["id"],
            "items": [{"product_id": product.id, "quantity": 1}],
        },
        headers=other_headers,
    )

    assert unauthenticated_response.status_code == 401
    assert empty_items_response.status_code == 422
    assert other_user_address_response.status_code == 404
    assert other_user_address_response.json()["detail"] == "Address not found"


def test_order_creation_rejects_inactive_products(
    client: TestClient,
    db_session: Session,
) -> None:
    headers = _register_and_login(client)
    address = _create_address(client, headers)
    inactive_product = Product(
        sku="PI-INACTIVE-ORDER-001",
        name="Inactive Product",
        description="Hidden from ordering.",
        price=Decimal("4.99"),
        is_active=False,
    )
    db_session.add(inactive_product)
    db_session.commit()
    db_session.refresh(inactive_product)

    response = client.post(
        "/api/v1/orders",
        json={
            "shipping_address_id": address["id"],
            "items": [{"product_id": inactive_product.id, "quantity": 1}],
        },
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_retrieve_list_and_filter_user_orders(
    client: TestClient,
    db_session: Session,
) -> None:
    products = seed_sample_products(db_session)
    headers = _register_and_login(client)
    address = _create_address(client, headers)
    pending_order = _create_order(
        client,
        headers,
        address_id=address["id"],
        product_id=products[0].id,
    )
    processing_order = _create_order(
        client,
        headers,
        address_id=address["id"],
        product_id=products[1].id,
    )
    db_order = db_session.get(Order, processing_order["id"])
    assert db_order is not None
    db_order.status = OrderStatus.PROCESSING
    db_session.commit()

    detail_response = client.get(f"/api/v1/orders/{pending_order['id']}", headers=headers)
    list_response = client.get("/api/v1/orders", headers=headers)
    filtered_response = client.get("/api/v1/orders?status=PENDING", headers=headers)

    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == pending_order["id"]
    assert list_response.status_code == 200
    assert {order["id"] for order in list_response.json()} == {
        pending_order["id"],
        processing_order["id"],
    }
    assert filtered_response.status_code == 200
    assert [order["id"] for order in filtered_response.json()] == [pending_order["id"]]


def test_order_ownership_is_enforced(client: TestClient, db_session: Session) -> None:
    product = seed_sample_products(db_session)[0]
    owner_headers = _register_and_login(client, email="owner@example.com")
    other_headers = _register_and_login(client, email="other@example.com")
    owner_address = _create_address(client, owner_headers)
    order = _create_order(
        client,
        owner_headers,
        address_id=owner_address["id"],
        product_id=product.id,
    )

    detail_response = client.get(f"/api/v1/orders/{order['id']}", headers=other_headers)
    cancel_response = client.post(
        f"/api/v1/orders/{order['id']}/cancel",
        headers=other_headers,
    )
    other_list_response = client.get("/api/v1/orders", headers=other_headers)

    assert detail_response.status_code == 404
    assert cancel_response.status_code == 404
    assert other_list_response.status_code == 200
    assert other_list_response.json() == []


def test_cancel_pending_order_and_reject_non_pending_cancel(
    client: TestClient,
    db_session: Session,
) -> None:
    product = seed_sample_products(db_session)[0]
    headers = _register_and_login(client)
    address = _create_address(client, headers)
    pending_order = _create_order(
        client,
        headers,
        address_id=address["id"],
        product_id=product.id,
    )
    processing_order = _create_order(
        client,
        headers,
        address_id=address["id"],
        product_id=product.id,
    )
    db_order = db_session.get(Order, processing_order["id"])
    assert db_order is not None
    db_order.status = OrderStatus.PROCESSING
    db_session.commit()

    cancel_response = client.post(
        f"/api/v1/orders/{pending_order['id']}/cancel",
        headers=headers,
    )
    non_pending_response = client.post(
        f"/api/v1/orders/{processing_order['id']}/cancel",
        headers=headers,
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "CANCELLED"
    assert non_pending_response.status_code == 400
    assert non_pending_response.json()["detail"] == "Only pending orders can be cancelled"


def test_admin_can_update_order_status_and_customer_cannot(
    client: TestClient,
    db_session: Session,
) -> None:
    product = seed_sample_products(db_session)[0]
    customer_headers = _register_and_login(client, email="customer@example.com")
    admin_headers = _register_and_login(client, email="admin@example.com")
    _promote_to_admin(db_session, "admin@example.com")
    address = _create_address(client, customer_headers)
    order = _create_order(
        client,
        customer_headers,
        address_id=address["id"],
        product_id=product.id,
    )

    customer_response = client.patch(
        f"/api/v1/orders/{order['id']}/status",
        json={"status": "SHIPPED"},
        headers=customer_headers,
    )
    admin_response = client.patch(
        f"/api/v1/orders/{order['id']}/status",
        json={"status": "SHIPPED"},
        headers=admin_headers,
    )

    assert customer_response.status_code == 403
    assert customer_response.json()["detail"] == "Admin access required"
    assert admin_response.status_code == 200
    assert admin_response.json()["status"] == "SHIPPED"


def test_admin_status_update_rejects_cancelled_orders(
    client: TestClient,
    db_session: Session,
) -> None:
    product = seed_sample_products(db_session)[0]
    customer_headers = _register_and_login(client, email="customer@example.com")
    admin_headers = _register_and_login(client, email="admin@example.com")
    _promote_to_admin(db_session, "admin@example.com")
    address = _create_address(client, customer_headers)
    order = _create_order(
        client,
        customer_headers,
        address_id=address["id"],
        product_id=product.id,
    )
    active_order = _create_order(
        client,
        customer_headers,
        address_id=address["id"],
        product_id=product.id,
    )
    cancel_response = client.post(
        f"/api/v1/orders/{order['id']}/cancel",
        headers=customer_headers,
    )
    assert cancel_response.status_code == 200

    cancelled_order_response = client.patch(
        f"/api/v1/orders/{order['id']}/status",
        json={"status": "DELIVERED"},
        headers=admin_headers,
    )
    cancel_status_response = client.patch(
        f"/api/v1/orders/{active_order['id']}/status",
        json={"status": "CANCELLED"},
        headers=admin_headers,
    )
    missing_order_response = client.patch(
        "/api/v1/orders/999/status",
        json={"status": "SHIPPED"},
        headers=admin_headers,
    )

    assert cancelled_order_response.status_code == 400
    assert cancelled_order_response.json()["detail"] == "Cancelled orders cannot be updated"
    assert cancel_status_response.status_code == 400
    assert (
        cancel_status_response.json()["detail"]
        == "Use the cancel endpoint to cancel pending orders"
    )
    assert missing_order_response.status_code == 404


def test_admin_report_lists_all_orders_with_status_filter(
    client: TestClient,
    db_session: Session,
) -> None:
    products = seed_sample_products(db_session)
    first_headers = _register_and_login(client, email="first@example.com")
    second_headers = _register_and_login(client, email="second@example.com")
    admin_headers = _register_and_login(client, email="admin@example.com")
    _promote_to_admin(db_session, "admin@example.com")
    first_address = _create_address(client, first_headers)
    second_address = _create_address(client, second_headers)
    pending_order = _create_order(
        client,
        first_headers,
        address_id=first_address["id"],
        product_id=products[0].id,
    )
    shipped_order = _create_order(
        client,
        second_headers,
        address_id=second_address["id"],
        product_id=products[1].id,
    )
    db_order = db_session.get(Order, shipped_order["id"])
    assert db_order is not None
    db_order.status = OrderStatus.SHIPPED
    db_session.commit()

    customer_response = client.get("/api/v1/reports/orders", headers=first_headers)
    report_response = client.get("/api/v1/reports/orders", headers=admin_headers)
    filtered_response = client.get(
        "/api/v1/reports/orders?status=PENDING",
        headers=admin_headers,
    )

    assert customer_response.status_code == 403
    assert report_response.status_code == 200
    assert {order["id"] for order in report_response.json()} == {
        pending_order["id"],
        shipped_order["id"],
    }
    assert filtered_response.status_code == 200
    assert [order["id"] for order in filtered_response.json()] == [pending_order["id"]]
    assert filtered_response.json()[0]["customer_email"] == "first@example.com"
    assert filtered_response.json()[0]["item_count"] == 1


def test_order_snapshots_do_not_change_after_address_or_product_updates(
    client: TestClient,
    db_session: Session,
) -> None:
    product = seed_sample_products(db_session)[0]
    headers = _register_and_login(client)
    address = _create_address(client, headers, city="Pune")
    order = _create_order(
        client,
        headers,
        address_id=address["id"],
        product_id=product.id,
    )

    address_response = client.patch(
        f"/api/v1/addresses/{address['id']}",
        json={"city": "Mumbai"},
        headers=headers,
    )
    assert address_response.status_code == 200
    product.name = "Renamed Keyboard"
    product.price = Decimal("49.99")
    db_session.commit()

    detail_response = client.get(f"/api/v1/orders/{order['id']}", headers=headers)

    assert detail_response.status_code == 200
    order_detail = detail_response.json()
    assert order_detail["shipping_city"] == "Pune"
    assert order_detail["items"][0]["product_name"] == "Mechanical Keyboard"
    assert order_detail["items"][0]["unit_price"] == "79.99"
