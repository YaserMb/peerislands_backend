# AI Usage

This project is being developed with AI assistance in an iterative workflow.

## Assistance Used So Far

- Interpreted the PRD into an implementation sequence.
- Added project setup files: `requirements.txt`, `.env.example`, and settings.
- Added configurable application logging and unhandled-error logging middleware.
- Implemented SQLAlchemy database foundation and Alembic migration setup.
- Filled local `.env`, applied migrations, and verified `app.db` tables.
- Implemented auth models, schemas, services, security helpers, and endpoints.
- Implemented product schema, service, endpoint, and sample product seed migration.
- Implemented saved-address schemas, service, endpoints, ownership enforcement,
  and default-address behavior.
- Implemented customer order schemas, service, endpoints, server-side totals,
  product/address snapshots, ownership enforcement, and pending cancellation.
- Added auth, product, address, and customer order endpoint tests with an
  isolated SQLite test database.
- Updated repo-local documentation as implementation milestones landed.

## Human Decisions

- Use SQLite first for local development.
- Keep PostgreSQL-ready configuration through `DATABASE_URL`.
- Start with authentication before product/address/order endpoints.
- Include `/api/v1/auth/me` with register/login to verify the JWT flow.
- Keep product catalog public/read-only for now.
- Require authentication and ownership checks for saved addresses.
- Make the first saved address default and clear sibling defaults when another
  address is selected as default.
- Keep customer order requests limited to address IDs, product IDs, and quantities;
  calculate all monetary totals on the server.
- Preserve historical orders by copying product and address snapshots at order
  creation time.

## Verification Performed

- Python compile checks for edited backend modules.
- SQLAlchemy metadata creation against SQLite.
- Alembic migration upgrade against temporary SQLite databases.
- Alembic metadata consistency check with `alembic check`.
- Local SQLite `app.db` migration version check.
- Auth endpoint tests with `pytest tests/test_auth.py`.
- Product endpoint tests with `pytest tests/test_products.py`.
- Address endpoint tests with `pytest tests/test_addresses.py`.
- Customer order endpoint tests with `pytest tests/test_orders.py`.
- Full suite with `pytest`.
- Logging setup import and runtime smoke checks.

## Notes

AI assistance has been used for scaffolding, implementation, documentation, and
verification. Final behavior should continue to be validated with tests as each
API area is implemented.
