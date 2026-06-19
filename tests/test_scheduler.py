from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.models.orders import Order, OrderStatus
from app.services.orders import process_pending_orders
from app.services.products import seed_sample_products
from app.services.scheduler import process_pending_orders_task


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


def _create_address(client: TestClient, headers: dict[str, str]) -> dict:
    response = client.post(
        "/api/v1/addresses",
        json={
            "full_name": "Yaser Basravi",
            "phone": "8668590057",
            "address_line1": "Flat 101, Example Apartments",
            "address_line2": "Baner",
            "city": "Pune",
            "state": "Maharashtra",
            "postal_code": "411045",
            "country": "India",
            "is_default": True,
        },
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


def test_process_pending_orders_updates_only_pending_orders(
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
    cancelled_order = _create_order(
        client,
        headers,
        address_id=address["id"],
        product_id=product.id,
    )
    cancelled_db_order = db_session.get(Order, cancelled_order["id"])
    assert cancelled_db_order is not None
    cancelled_db_order.status = OrderStatus.CANCELLED
    db_session.commit()

    processed_count = process_pending_orders(db_session)

    db_session.expire_all()
    assert processed_count == 1
    assert db_session.get(Order, pending_order["id"]).status == OrderStatus.PROCESSING
    assert db_session.get(Order, cancelled_order["id"]).status == OrderStatus.CANCELLED


def test_process_pending_orders_task_uses_session_factory(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    product = seed_sample_products(db_session)[0]
    headers = _register_and_login(client)
    address = _create_address(client, headers)
    order = _create_order(
        client,
        headers,
        address_id=address["id"],
        product_id=product.id,
    )
    monkeypatch.setattr("app.services.scheduler.SessionLocal", lambda: db_session)

    processed_count = process_pending_orders_task.run()

    db_session.expire_all()
    assert processed_count == 1
    assert db_session.get(Order, order["id"]).status == OrderStatus.PROCESSING


def test_celery_beat_schedules_pending_order_processing() -> None:
    schedule = celery_app.conf.beat_schedule["process-pending-orders-every-5-minutes"]

    assert schedule["task"] == "app.services.scheduler.process_pending_orders_task"
    assert schedule["schedule"] == settings.pending_order_processing_interval_seconds
