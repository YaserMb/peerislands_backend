# Backend — Agent Guide

This file gives AI coding agents a quick, repo-local guide for working in this
FastAPI backend. The product target is documented in `PRD.md`.

## Token-Efficient Start

- If the user gives exact files, start with those files.
- Otherwise read `REPO_MAP.md` first to find the relevant area.
- Read `PRD.md` when the task depends on product behavior, acceptance criteria,
  database shape, or endpoint contracts.
- For small tasks, read only the target file and its direct dependencies.

## Scope

Use this backend for an e-commerce order processing API:

- FastAPI endpoints
- SQLAlchemy models and database session setup
- Pydantic request/response schemas
- service-layer business rules
- JWT authentication and password hashing
- Alembic migrations
- APScheduler background jobs
- pytest API and service tests

## Current State

The project is still a scaffold.

- Config, logging, database models, Alembic, SQLite setup, and auth are done.
- `app/api/v1/auth.py` provides register, login, and current-user endpoints.
- `tests/test_auth.py` covers the implemented auth endpoints with an isolated
  SQLite test database.
- `PRD.md` is the source of truth for the intended backend behavior.
- `README.md` and `AI_USAGE.md` document setup, verification, and AI-assisted
  development notes.
- Product, address, order, report, scheduler, and broader tests still need to
  be added.

## Build Verification

Once the project has dependencies and tests, run:

```bash
python -m pytest
```

For migration work, also run:

```bash
alembic upgrade head
```

For local API smoke testing, run the app with:

```bash
uvicorn app.main:app --reload
```

## Critical Rules

- Keep API behavior aligned with `PRD.md`.
- Put business rules in services, not directly inside route handlers.
- Calculate order totals, line totals, and copied product/address snapshots on
  the server.
- Never trust client-submitted prices or totals.
- Enforce ownership for addresses and orders.
- Restrict admin report and order-status updates to admin users.
- Hash passwords before storage.
- Add pytest coverage for every new or modified endpoint.
- Mock external services if any are introduced.
- Keep migrations reproducible and committed with model changes.

## Repo-Local Skills

Check for a matching project-local skill before making broad workflow changes.

| Skill | Use when | Path |
|-------|----------|------|
| `update-docs` | Updating docs after backend, schema, test, setup, or workflow changes | `skills/update-docs/SKILL.md` |

## Expected Architecture

Prefer this shape as implementation grows:

```text
app/
  main.py
  api/
    v1/
      api.py
      auth.py
      products.py
      addresses.py
      orders.py
      reports.py
  core/
    config.py
    security.py
    logging.py
  db/
    base.py
    session.py
    models/
  schemas/
    users.py
    auth.py
    orders.py
  services/
    users.py
    auth.py
    orders.py
    scheduler.py
tests/
alembic/
```

Register new route modules through `app/api/v1/api.py`, then mount that router
from `app/main.py`.
