# Order Processing Backend

FastAPI backend for the e-commerce order processing API described in `PRD.md`.

## Current Status

Implemented:

- SQLite-first configuration through `.env`
- Local `app.db` can be created by applying Alembic migrations
- Configurable application logging with unhandled-error stack traces
- SQLAlchemy models for users, products, addresses, orders, and order items
- Alembic migration foundation with an initial schema migration
- Authentication endpoints for register, login, and current user
- Product listing endpoint with seeded sample products
- Saved-address create/list/retrieve/update/delete endpoints
- Address ownership enforcement and default-address behavior
- Customer order create/list/detail/cancel endpoints
- Admin order status update endpoint
- Admin order report endpoint with optional status filtering
- Server-side order total calculation with product and address snapshots
- Celery Beat + Redis scheduled processing for pending orders
- Pytest coverage for auth, products, addresses, customer orders, and scheduler logic

## Setup

Create or activate a virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

For the existing local venv in this workspace:

```bash
venv/bin/pip install -r requirements.txt
```

Create a local environment file:

```bash
cp .env.example .env
```

The default local database is SQLite:

```text
DATABASE_URL=sqlite:///./app.db
```

Logging defaults to `INFO`:

```text
LOG_LEVEL=INFO
```

Celery uses Redis for scheduled background processing:

```text
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
PENDING_ORDER_PROCESSING_INTERVAL_SECONDS=300
```

## Database

Apply migrations before running the API against the local database:

```bash
venv/bin/alembic upgrade head
```

This creates/updates the ignored local SQLite database file at `app.db` and
seeds the sample product catalog used for order creation.

Create a new migration after model changes:

```bash
venv/bin/alembic revision --autogenerate -m "describe change"
```

Check whether model metadata and migrations are in sync:

```bash
venv/bin/alembic check
```

## Run

Start the development server:

```bash
venv/bin/uvicorn app.main:app --reload
```

Open the Swagger UI at:

```text
http://127.0.0.1:8000/docs
```

## Background Jobs

Pending orders are processed by Celery Beat and a Celery worker using Redis.
The task updates `PENDING` orders to `PROCESSING` every 300 seconds.

Start Redis locally, then run the worker and beat in separate terminals:

```bash
venv/bin/celery -A app.core.celery_app:celery_app worker --loglevel=info
venv/bin/celery -A app.core.celery_app:celery_app beat --loglevel=info
```

The reusable processing logic lives in `app.services.orders.process_pending_orders`
so tests can validate it without waiting for Celery Beat.

## Auth Endpoints

Register:

```http
POST /api/v1/auth/register
```

```json
{
  "name": "Yaser Basravi",
  "email": "yaser@example.com",
  "password": "secure-password"
}
```

Login:

```http
POST /api/v1/auth/login
```

This endpoint uses OAuth2 form data:

```text
username=yaser@example.com
password=secure-password
```

Current user:

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

## Product Endpoints

List active products:

```http
GET /api/v1/products
```

Products are seeded by Alembic so a fresh local database has orderable sample
items after:

```bash
venv/bin/alembic upgrade head
```

Seeded products:

- `PI-KEYBOARD-001` - Mechanical Keyboard - `79.99`
- `PI-MOUSE-001` - Wireless Mouse - `29.99`
- `PI-HEADSET-001` - Noise-Cancelling Headset - `119.99`

Users, saved addresses, and orders are not seeded. Create them through the auth,
address, and order API endpoints.

## Address Endpoints

All address endpoints require:

```http
Authorization: Bearer <access_token>
```

Create address:

```http
POST /api/v1/addresses
```

```json
{
  "full_name": "Yaser Basravi",
  "phone": "8668590057",
  "address_line1": "Flat 101, Example Apartments",
  "address_line2": "Baner",
  "city": "Pune",
  "state": "Maharashtra",
  "postal_code": "411045",
  "country": "India",
  "is_default": true
}
```

List saved addresses:

```http
GET /api/v1/addresses
```

Retrieve one address:

```http
GET /api/v1/addresses/{address_id}
```

Update address:

```http
PATCH /api/v1/addresses/{address_id}
```

Delete address:

```http
DELETE /api/v1/addresses/{address_id}
```

Address rules:

- Users can only access their own saved addresses.
- Accessing another user's address returns `404`.
- The first saved address becomes default.
- Setting one address as default clears the user's other default addresses.

## Order Endpoints

All order endpoints require:

```http
Authorization: Bearer <access_token>
```

Create an order:

```http
POST /api/v1/orders
```

```json
{
  "shipping_address_id": 1,
  "items": [
    {
      "product_id": 1,
      "quantity": 2
    },
    {
      "product_id": 2,
      "quantity": 1
    }
  ]
}
```

List your orders:

```http
GET /api/v1/orders
GET /api/v1/orders?status=PENDING
```

Retrieve one order:

```http
GET /api/v1/orders/{order_id}
```

Cancel a pending order:

```http
POST /api/v1/orders/{order_id}/cancel
```

Admin update order status:

```http
PATCH /api/v1/orders/{order_id}/status
```

```json
{
  "status": "SHIPPED"
}
```

Admin order report:

```http
GET /api/v1/reports/orders
GET /api/v1/reports/orders?status=PENDING
```

Order rules:

- Users can only access their own orders.
- Accessing another user's order returns `404`.
- New orders start as `PENDING`.
- Only `PENDING` orders can be cancelled.
- Only admin users can update operational statuses or access the all-order report.
- `CANCELLED` orders cannot be updated through the status endpoint.
- Product prices, line totals, and order totals are calculated server-side.
- Product name/unit price and shipping address fields are copied into order snapshots.

## Tests

Run targeted tests:

```bash
venv/bin/python -m pytest tests/test_auth.py
venv/bin/python -m pytest tests/test_products.py
venv/bin/python -m pytest tests/test_addresses.py
venv/bin/python -m pytest tests/test_orders.py
venv/bin/python -m pytest tests/test_scheduler.py
```

Run the full test suite:

```bash
venv/bin/python -m pytest
```
