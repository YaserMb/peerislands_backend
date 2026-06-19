# Repo Map: Order Processing Backend

Last updated: 2026-06-19

## 1) Purpose

This backend is intended to implement the e-commerce order processing API
described in `PRD.md`.

Target capabilities:

- customer registration and JWT login
- product catalog listing
- saved shipping addresses
- multi-item order creation
- order detail and order listing
- order cancellation rules
- admin order status updates and reporting
- scheduled pending-order processing
- Alembic migrations
- pytest coverage

## 2) Current Top-Level Layout

```text
backend/
  .env.example
  AGENTS.md
  AI_CONTEXT.md
  AI_USAGE.md
  PRD.md
  README.md
  REPO_MAP.md
  requirements.txt
  alembic.ini
  alembic/
    env.py
    script.py.mako
    versions/
      20260618_0001_create_initial_tables.py
      20260618_0002_seed_sample_products.py
  skills/
    update-docs/
      SKILL.md
  app/
    main.py
    api/
      __init__.py
      v1/
        __init__.py
        addresses.py
        api.py
        auth.py
        orders.py
        products.py
    core/
      config.py
      logging.py
      security.py
    db/
      base.py
      session.py
      models/
        addresses.py
        orders.py
        products.py
        users.py
    schemas/
      addresses.py
      auth.py
      orders.py
      products.py
      users.py
    services/
      addresses.py
      auth.py
      orders.py
      products.py
      users.py
  test/
  tests/
    conftest.py
    test_addresses.py
    test_auth.py
    test_orders.py
    test_products.py
  venv/
```

## 3) Current Implementation Snapshot

| Path | Current role |
|------|--------------|
| `skills/update-docs/SKILL.md` | Project-local skill for keeping docs current after meaningful changes. |
| `PRD.md` | Product and technical requirements. This is the source of truth. |
| `README.md` | Human setup, migration, run, auth endpoint, and test instructions. |
| `AI_CONTEXT.md` | Backend behavior context covering API flows, product catalog logic, persistence, and verification. |
| `AI_USAGE.md` | Summary of AI-assisted implementation work and verification performed. |
| `AGENTS.md` | Instructions for AI coding agents working in this backend. |
| `REPO_MAP.md` | This file; quick navigation guide. |
| `requirements.txt` | Python dependencies for FastAPI, SQLAlchemy, Alembic, auth, scheduler, and tests. |
| `.env.example` | Documented local environment variables; defaults to SQLite at `sqlite:///./app.db`. |
| `.gitignore` | Ignores `.env`, virtualenvs, Python build artifacts, and local SQLite database files. |
| `alembic.ini` | Alembic configuration using `alembic/` as the migration script location. |
| `alembic/env.py` | Alembic runtime setup that loads `DATABASE_URL` from application settings and uses `Base.metadata`. |
| `alembic/versions/20260618_0001_create_initial_tables.py` | Initial migration for users, products, addresses, orders, and order items. |
| `alembic/versions/20260618_0002_seed_sample_products.py` | Seed migration that inserts active sample products for local order creation. |
| `app/main.py` | FastAPI app setup that mounts the versioned API router and keeps a temporary `/test` endpoint. |
| `app/api/v1/api.py` | Central v1 router registration. |
| `app/api/v1/addresses.py` | Authenticated saved-address CRUD endpoints under `/api/v1/addresses`. |
| `app/api/v1/auth.py` | Register, login, and current-user endpoints under `/api/v1/auth`. |
| `app/api/v1/orders.py` | Authenticated customer order create/list/detail/cancel endpoints under `/api/v1/orders`. |
| `app/api/v1/products.py` | Public active product listing endpoint under `/api/v1/products`. |
| `app/core/config.py` | Pydantic settings loaded from `.env`, including SQLite-first database URL, log level, JWT settings, and CORS origins. |
| `app/core/security.py` | Password hashing, JWT creation/validation, and current-user dependency. |
| `app/core/logging.py` | Application logging setup for app, Uvicorn, access, and SQLAlchemy loggers. |
| `app/db/base.py` | SQLAlchemy declarative base plus model module imports for Alembic metadata discovery. |
| `app/db/session.py` | SQLAlchemy engine, session factory, and `get_db` dependency using configured `DATABASE_URL`. |
| `app/db/models/users.py` | `User` model and `UserRole` enum. |
| `app/db/models/products.py` | `Product` model with non-negative price constraint. |
| `app/db/models/addresses.py` | `Address` model for saved shipping addresses. |
| `app/db/models/orders.py` | `Order`, `OrderItem`, and `OrderStatus` models with snapshot fields and amount constraints. |
| `app/schemas/addresses.py` | Address create, partial update, and public read schemas. |
| `app/schemas/auth.py` | Token response schema. |
| `app/schemas/products.py` | Public product read schema. |
| `app/schemas/users.py` | User registration and public user response schemas. |
| `app/schemas/orders.py` | Order create, item create, item read, and full order read schemas. |
| `app/services/addresses.py` | Address ownership queries, CRUD operations, and default-address behavior. |
| `app/services/auth.py` | Registration and login authentication helpers. |
| `app/services/products.py` | Active product listing, active-product lookup, and sample product seed helper. |
| `app/services/users.py` | User lookup and creation helpers. |
| `app/services/orders.py` | Customer order creation, server-side totals, snapshots, listing, detail lookup, and pending cancellation rules. |
| `tests/conftest.py` | Isolated SQLite database and FastAPI test client fixtures. |
| `tests/test_addresses.py` | Address CRUD, authentication, ownership, and default-address coverage. |
| `tests/test_auth.py` | Register, duplicate registration, login, bad login, and current-user auth coverage. |
| `tests/test_orders.py` | Customer order creation, validation, ownership, listing, filtering, cancellation, and snapshot coverage. |
| `tests/test_products.py` | Product listing and product service seed/active-lookup coverage. |
| `test/` | Legacy empty test directory; prefer `tests/` for new pytest files. |

## 4) Files To Add

### API layer

| Path | Purpose |
|------|---------|
| `app/api/v1/reports.py` | Admin order report endpoint. |
| `app/api/v1/orders.py` | Admin order status-update endpoint extension. |

### Services

| Path | Purpose |
|------|---------|
| `app/services/scheduler.py` | `process_pending_orders` job function. |

### Tests

| Path | Purpose |
|------|---------|
| `tests/test_reports.py` | Admin-only all-orders report. |
| `tests/test_scheduler.py` | Pending-to-processing background job logic. |

## 5) Task-To-File Index

| Task | Start with |
|------|------------|
| Understand product behavior | `PRD.md` |
| App startup/routing | `app/main.py`, then `app/api/v1/api.py` once created |
| Auth work | `app/core/security.py`, `app/api/v1/auth.py`, `app/services/auth.py` |
| Database models | `app/db/models/`, `app/db/base.py`, Alembic migration files |
| Order creation/cancellation | `app/services/orders.py`, `app/api/v1/orders.py`, `app/schemas/orders.py` |
| Address CRUD | `app/services/addresses.py`, `app/api/v1/addresses.py`, `app/schemas/addresses.py` |
| Product catalog | `app/services/products.py`, `app/api/v1/products.py`, `app/db/models/products.py` |
| Admin reporting | `app/api/v1/reports.py`, `app/services/orders.py` |
| Background processing | `app/services/scheduler.py`, app startup scheduler wiring |
| Tests | Matching file under `tests/` |

## 6) Implementation Order

1. Add dependency/config/session scaffolding.
2. Add SQLAlchemy models and Alembic migration.
3. Add auth and current-user dependencies.
4. Add product seed/listing path. (done)
5. Add address CRUD. (done)
6. Add customer order create/list/detail/cancel behavior. (done)
7. Add admin order status/report behavior.
8. Add APScheduler startup/shutdown wiring and testable job service.
9. Add remaining pytest coverage for admin reports, status updates, and scheduler behavior.
10. Keep README and AI_USAGE updated as user-facing behavior expands.

## 7) Notes

- `PRD.md` currently jumps from section 8 to section 10; fix numbering when
  documentation is refreshed.
- Use `Decimal` for money fields.
- Do not accept prices, line totals, or order totals from clients.
- Copy product and address snapshots when creating orders.
- Keep customer-facing endpoints scoped to the authenticated user.
