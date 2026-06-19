# Order Processing Backend

FastAPI backend for the e-commerce order processing API described in `PRD.md`.

## Current Status

Implemented:

- SQLite-first configuration through `.env`
- Configurable application logging with unhandled-error stack traces
- SQLAlchemy models for users, products, addresses, orders, and order items
- Alembic migration foundation with an initial schema migration
- Authentication endpoints for register, login, and current user
- Pytest coverage for the auth flow

Still pending:

- product listing
- address CRUD
- order create/list/detail/cancel/status/report endpoints
- scheduler job for pending orders
- broader API test coverage

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

## Database

Apply migrations before running the API against the local database:

```bash
venv/bin/alembic upgrade head
```

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

## Tests

Run the implemented auth tests:

```bash
venv/bin/python -m pytest tests/test_auth.py
```

Run the full test suite:

```bash
venv/bin/python -m pytest
```
