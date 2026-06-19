# Backend AI Context

Last synthesized: 2026-06-19

## Quick Start

| Need | Read |
|------|------|
| API routing and endpoint behavior | §2 API Surface |
| Product catalog behavior | §3 Product Catalog Flow |
| Address management behavior | §4 Address Management Flow |
| Customer order behavior | §5 Customer Order Flow |
| Background processing | §6 Background Processing |
| Database and migrations | §7 Persistence |
| Test expectations | §8 Verification |

## §1 Purpose

This backend implements an e-commerce order processing API with FastAPI,
SQLAlchemy, Alembic, JWT authentication, and pytest coverage. The domain is
centered on users, products, addresses, orders, and order items.

## §2 API Surface

Implemented endpoints:

- `POST /api/v1/auth/register` creates a customer account.
- `POST /api/v1/auth/login` returns a bearer token using OAuth2 password form data.
- `GET /api/v1/auth/me` returns the authenticated user.
- `GET /api/v1/products` returns active products that can be ordered.
- `POST /api/v1/addresses` creates a saved address for the authenticated user.
- `GET /api/v1/addresses` lists the authenticated user's saved addresses.
- `GET /api/v1/addresses/{address_id}` returns one owned address.
- `PATCH /api/v1/addresses/{address_id}` updates one owned address.
- `DELETE /api/v1/addresses/{address_id}` deletes one owned address.
- `POST /api/v1/orders` creates a pending multi-item order for the authenticated user.
- `GET /api/v1/orders` lists the authenticated user's orders, optionally filtered by `status`.
- `GET /api/v1/orders/{order_id}` returns one owned order with items.
- `POST /api/v1/orders/{order_id}/cancel` cancels one owned pending order.

Pending endpoint groups:

- Admin order status update flow.
- Admin reports.

## §3 Product Catalog Flow

Products are persisted in the `products` table and exposed through a public
read-only catalog endpoint.

```text
GET /api/v1/products
  -> app/api/v1/products.py
  -> app/services/products.py:list_active_products
  -> Product rows where is_active = true, ordered by id
  -> app/schemas/products.py:ProductRead
```

Rules:

- Only active products are returned from the catalog.
- Product prices are represented as `Decimal`/`Numeric(12, 2)`.
- Product creation and update APIs are intentionally not implemented yet.
- `get_active_product_by_id` is available for order creation so inactive
  products cannot be ordered.

## §4 Address Management Flow

Address endpoints require a bearer token and always scope data to the current
user.

```text
Authorization: Bearer <token>
  -> app/core/security.py:get_current_user
  -> app/api/v1/addresses.py
  -> app/services/addresses.py
  -> Address rows where user_id = current_user.id
  -> app/schemas/addresses.py:AddressRead
```

Rules:

- Users can create, list, retrieve, update, and delete only their own addresses.
- Accessing another user's address returns `404 Address not found`.
- The first saved address becomes default even when `is_default` is omitted or false.
- Setting an address as default clears the user's other default addresses.
- Updating saved addresses does not alter existing order snapshots.

## §5 Customer Order Flow

Order endpoints require a bearer token and always scope data to the current user.

```text
POST /api/v1/orders
  -> app/api/v1/orders.py
  -> app/services/orders.py:create_order
  -> validates owned address and active products
  -> calculates unit prices, line totals, and order total server-side
  -> copies product and shipping address snapshots
  -> app/schemas/orders.py:OrderRead
```

Rules:

- Clients submit only `shipping_address_id`, `product_id`, and `quantity`.
- New orders start in `PENDING`.
- Users can list, filter, retrieve, and cancel only their own orders.
- Accessing another user's order returns `404 Order not found`.
- Only `PENDING` orders can be cancelled.
- Inactive products cannot be ordered.

## §6 Background Processing

Celery Beat schedules pending-order processing through Redis every 300 seconds.

```text
app/core/celery_app.py
  -> broker/result backend from CELERY_BROKER_URL and CELERY_RESULT_BACKEND
  -> beat task app.services.scheduler.process_pending_orders_task

app/services/scheduler.py
  -> opens SessionLocal
  -> app/services/orders.py:process_pending_orders
  -> closes the session
```

Rules:

- The Celery task is only a DB-session wrapper.
- The reusable service updates `PENDING` orders to `PROCESSING` and returns the processed count.
- Tests call the service/task directly and do not require a running Redis server.

## §7 Persistence

Alembic migrations define the database shape and seed local orderable products.

- `20260618_0001_create_initial_tables.py` creates users, products, addresses,
  orders, and order items.
- `20260618_0002_seed_sample_products.py` inserts active sample products so
  orders can be created against a fresh local database.

The product seed data currently includes:

- `PI-KEYBOARD-001`
- `PI-MOUSE-001`
- `PI-HEADSET-001`

Only products are seeded. Users, saved addresses, and orders are created through
the API during normal use or in tests.

## §8 Verification

Current pytest coverage includes:

- Auth registration, duplicate email handling, login, bad login, and current user.
- Product listing returns active seeded products.
- Inactive products are excluded from the catalog.
- Product seed helper is idempotent.
- Active-product lookup ignores inactive products.
- Address create/list/retrieve/update/delete.
- Address authentication requirement.
- Address ownership enforcement across retrieve/update/delete.
- Default-address behavior when creating and updating saved addresses.
- Customer order creation with multiple items and server-side totals.
- Order authentication, validation, ownership, listing, status filtering, cancellation,
  inactive-product rejection, and snapshot stability.
- Celery Beat schedule configuration, task wrapper behavior, and pending-order
  processing service behavior.

Run verification from `backend/`:

```bash
venv/bin/python -m pytest
venv/bin/alembic upgrade head
```
