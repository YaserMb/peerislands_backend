from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.products import Product
from app.services.products import (
    SAMPLE_PRODUCTS,
    get_active_product_by_id,
    seed_sample_products,
)


def test_list_products_returns_seeded_active_products(
    client: TestClient,
    db_session: Session,
) -> None:
    seeded_products = seed_sample_products(db_session)
    inactive_product = Product(
        sku="PI-ARCHIVE-001",
        name="Archived Product",
        description="Not available for ordering.",
        price=Decimal("9.99"),
        is_active=False,
    )
    db_session.add(inactive_product)
    db_session.commit()

    response = client.get("/api/v1/products")

    assert response.status_code == 200
    product_page = response.json()
    products = product_page["items"]
    assert product_page["page"] == 1
    assert product_page["page_size"] == 20
    assert product_page["total"] == len(SAMPLE_PRODUCTS)
    assert product_page["total_pages"] == 1
    assert len(products) == len(SAMPLE_PRODUCTS)
    assert [product["sku"] for product in products] == [
        product.sku for product in seeded_products
    ]
    assert inactive_product.sku not in {product["sku"] for product in products}
    assert products[0] == {
        "id": seeded_products[0].id,
        "sku": "PI-KEYBOARD-001",
        "name": "Mechanical Keyboard",
        "description": "Compact mechanical keyboard with hot-swappable switches.",
        "price": "79.99",
        "is_active": True,
        "created_at": seeded_products[0].created_at.isoformat(),
        "updated_at": seeded_products[0].updated_at.isoformat(),
    }

    paginated_response = client.get("/api/v1/products?page=2&page_size=2")
    assert paginated_response.status_code == 200
    paginated_page = paginated_response.json()
    assert paginated_page["total"] == len(SAMPLE_PRODUCTS)
    assert paginated_page["total_pages"] == 2
    assert [product["sku"] for product in paginated_page["items"]] == [
        seeded_products[2].sku
    ]


def test_seed_sample_products_is_idempotent(db_session: Session) -> None:
    first_seed = seed_sample_products(db_session)
    second_seed = seed_sample_products(db_session)

    assert [product.id for product in second_seed] == [product.id for product in first_seed]
    assert db_session.query(Product).count() == len(SAMPLE_PRODUCTS)


def test_get_active_product_by_id_ignores_inactive_products(db_session: Session) -> None:
    active_product = seed_sample_products(db_session)[0]
    inactive_product = Product(
        sku="PI-INACTIVE-001",
        name="Inactive Product",
        description="Hidden from the catalog.",
        price=Decimal("4.99"),
        is_active=False,
    )
    db_session.add(inactive_product)
    db_session.commit()

    assert get_active_product_by_id(db_session, active_product.id) == active_product
    assert get_active_product_by_id(db_session, inactive_product.id) is None
