# Product Requirements Document: Order Processing System

## 1. Objective

Build a backend API for an E-commerce Order Processing System. The system should allow authenticated customers to place orders, track order status, list their orders, and cancel eligible orders. The backend should also include a scheduled background process that automatically updates pending orders to processing every 5 minutes.

The project should demonstrate clean backend architecture, validation, persistence, authentication, migrations, scheduled jobs, and automated tests.

## 2. Scope

### In Scope

- FastAPI backend API
- User/customer model
- JWT-based authentication
- Product/item model for orderable items
- Address model for customer shipping addresses
- Order creation with multiple items
- Order retrieval by ID
- Order listing with optional status filter
- Order status updates
- Order cancellation rules
- Background job to process pending orders
- Database migrations
- API validation and error handling
- Automated tests
- API documentation through Swagger/OpenAPI
- Documentation for AI-assisted development


## 3. Requirement Interpretation

The requirement "create an order with multiple items" requires an `order_items` table. Each order must store the items purchased at the time the order was placed.

A cart is not required by the original assignment because customers can create an order directly by submitting multiple items in the order request. The assignment focuses on order processing, not shopping-cart management.

Because the order lifecycle includes `SHIPPED` and `DELIVERED`, a shipping address is a practical addition. The system should allow users to save addresses and select one when creating an order.

Recommended implementation:

- Must have: `orders` and `order_items`
- Good additions: `users`, `products`, and `addresses`
- Not needed for this assignment: `carts` and `cart_items`

The API should still support direct order creation so the assignment requirement remains simple to test.

## 4. Recommended Tech Stack

- Language: Python
- Framework: FastAPI
- ORM: SQLAlchemy
- Validation: Pydantic
- Database: SQLite for local development, PostgreSQL-ready configuration
- Migrations: Alembic
- Authentication: JWT using OAuth2 password flow
- Password hashing: passlib with bcrypt
- Background scheduler: Celery Beat with Redis
- Testing: pytest and FastAPI TestClient
- API docs: FastAPI Swagger UI at `/docs`

## 5. Core Domain Model

### User

Represents a customer who can place orders.

Fields:

- `id`
- `name`
- `email`
- `hashed_password`
- `role`
- `created_at`
- `updated_at`

Rules:

- Email must be unique.
- Password must be stored as a hash.
- Orders must belong to a valid user.
- Supported roles: `CUSTOMER` and `ADMIN`.
- New registered users default to `CUSTOMER`.

### Product

Represents an item that can be purchased.

Fields:

- `id`
- `sku`
- `name`
- `description`
- `price`
- `is_active`
- `created_at`
- `updated_at`

Rules:

- SKU must be unique.
- Price must be greater than or equal to 0.
- Only active products can be ordered.

Note:

- Product catalog management is intentionally minimal for this assignment.
- Products may be seeded through a migration or setup script.

### Address

Represents a saved customer address that can be used as a shipping address.

Fields:

- `id`
- `user_id`
- `full_name`
- `phone`
- `address_line1`
- `address_line2`
- `city`
- `state`
- `postal_code`
- `country`
- `is_default`
- `created_at`
- `updated_at`

Rules:

- Address must belong to a valid user.
- Users can have multiple saved addresses.
- A user may have one default address.

### Order

Represents a customer order.

Fields:

- `id`
- `user_id`
- `shipping_address_id`
- `status`
- `total_amount`
- `shipping_full_name`
- `shipping_phone`
- `shipping_address_line1`
- `shipping_address_line2`
- `shipping_city`
- `shipping_state`
- `shipping_postal_code`
- `shipping_country`
- `created_at`
- `updated_at`

Statuses:

- `PENDING`
- `PROCESSING`
- `SHIPPED`
- `DELIVERED`
- `CANCELLED`

Rules:

- New orders start in `PENDING` status.
- Total amount must be calculated server-side.
- Orders can only be cancelled when status is `PENDING`.
- Background job updates `PENDING` orders to `PROCESSING`.
- Shipping address fields should be copied onto the order at order creation time so historical order data remains stable even if the saved address changes later.

### OrderItem

Represents an item inside an order.

Fields:

- `id`
- `order_id`
- `product_id`
- `product_name`
- `quantity`
- `unit_price`
- `line_total`

Rules:

- An order must have at least one item.
- Quantity must be greater than 0.
- Unit price must be greater than or equal to 0.
- Line total must be calculated server-side.
- Product name and unit price should be copied onto the order item at order creation time so historical order data remains stable even if the product changes later.

## 6. API Requirements

### Authentication

#### Register User

`POST /auth/register`

Creates a new user account.

Request:

```json
{
  "name": "Yaser Basravi",
  "email": "yaser@example.com",
  "password": "secure-password"
}
```

Response:

```json
{
  "id": 1,
  "name": "Yaser Basravi",
  "email": "yaser@example.com"
}
```

#### Login

`POST /auth/login`

Authenticates a user and returns a JWT access token.

Response:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

#### Get Current User

`GET /auth/me`

Returns the authenticated user profile.

Authentication:

- Requires `Authorization: Bearer <token>`

### Orders

#### Create Order

`POST /orders`

Creates an order for the authenticated user.

Authentication:

- Required

Request:

```json
{
  "shipping_address_id": 1,
  "items": [
    {
      "product_id": 1,
      "quantity": 2
    }
  ]
}
```

Expected behavior:

- Create order in `PENDING` status.
- Calculate item line totals.
- Calculate order total.
- Associate order with authenticated user.
- Validate that the shipping address belongs to the authenticated user.
- Copy shipping address fields onto the order.
- Copy product name and current unit price into order items.

#### Retrieve Order Details

`GET /orders/{order_id}`

Returns order details including customer and items.

Authentication:

- Required

Rules:

- Customer can retrieve only their own orders.
- Return `404` if order does not exist.

#### List Orders

`GET /orders`

Optional filter:

`GET /orders?status=PENDING`

Authentication:

- Required

Rules:

- Return only the authenticated user's orders.
- If status is provided, filter by status.

This endpoint satisfies the customer-facing order tracking requirement.

#### List All Orders Report

`GET /reports/orders`

Optional filter:

`GET /reports/orders?status=PENDING`

Authentication:

- Required
- Admin only

Rules:

- Return all orders across all customers.
- If status is provided, filter by status.
- Include customer, order total, status, created date, and item count.

This endpoint satisfies the system-level "list all orders, optionally filtered by status" requirement without allowing customers to see other customers' orders.

#### Update Order Status

`PATCH /orders/{order_id}/status`

Updates the status of an order.

Authentication:

- Required

Request:

```json
{
  "status": "SHIPPED"
}
```

Rules:

- Validate status value.
- Do not allow status changes for `CANCELLED` orders.
- Return `404` if order does not exist.

Note:

- This endpoint should be restricted to `ADMIN` users because order status transitions such as `SHIPPED` and `DELIVERED` are operational actions.

#### Cancel Order

`POST /orders/{order_id}/cancel`

Cancels an order.

Authentication:

- Required

Rules:

- Only `PENDING` orders can be cancelled.
- If order is already `PROCESSING`, `SHIPPED`, `DELIVERED`, or `CANCELLED`, return a validation error.

### Addresses

#### Create Address

`POST /addresses`

Creates a saved address for the authenticated user.

Authentication:

- Required

Request:

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

#### List Addresses

`GET /addresses`

Returns saved addresses for the authenticated user.

Authentication:

- Required

#### Retrieve Address

`GET /addresses/{address_id}`

Returns one saved address.

Authentication:

- Required

Rules:

- Address must belong to authenticated user.

#### Update Address

`PATCH /addresses/{address_id}`

Updates a saved address.

Authentication:

- Required

Rules:

- Address must belong to authenticated user.
- Updating a saved address must not change old orders because orders store a shipping address snapshot.

#### Delete Address

`DELETE /addresses/{address_id}`

Deletes a saved address.

Authentication:

- Required

Rules:

- Address must belong to authenticated user.
- Existing orders should remain valid because they store a shipping address snapshot.

### Products

#### List Products

`GET /products`

Returns active products that can be ordered.

Authentication:

- Optional

Note:

- Product creation/update APIs are not required unless extra admin functionality is desired.

## 7. Background Job Requirements

The system must run a scheduled background job every 5 minutes.

Job:

```text
process_pending_orders
```

Behavior:

- Find all orders with status `PENDING`.
- Update them to `PROCESSING`.
- Persist changes to the database.

Implementation:

- Use Celery Beat for scheduling.
- Use Redis as the Celery broker and result backend.
- Keep job logic inside a service function so it can be tested directly.
- Keep the Celery task wrapper responsible for opening and closing its own database session.

Production note:

- Celery worker and beat processes should run separately from the FastAPI web process so background processing can scale independently.

## 8. Database and Migration Requirements

Use Alembic for database migrations.

Required migration:

- Create `users` table.
- Create `products` table.
- Create `addresses` table.
- Create `orders` table.
- Create `order_items` table.
- Add indexes for commonly queried fields:
  - `users.email`
  - `users.role`
  - `products.sku`
  - `addresses.user_id`
  - `orders.user_id`
  - `orders.shipping_address_id`
  - `orders.status`

Expected commands:

```bash
alembic revision --autogenerate -m "create users and orders tables"
alembic upgrade head
```

The project should include:

- `alembic.ini`
- `alembic/`
- Initial migration file



## 10. Validation and Error Handling

Expected API behavior:

- Return `400` for invalid business operations.
- Return `401` for missing or invalid authentication.
- Return `404` for missing resources.
- Return `409` for duplicate user email.
- Return `409` for duplicate product SKU.
- Return structured error messages.

Examples:

```json
{
  "detail": "Only pending orders can be cancelled"
}
```

```json
{
  "detail": "Order not found"
}
```

## 11. Testing Requirements

Automated tests should cover:

- User registration
- Duplicate email registration
- User login
- List active products
- Create address
- List authenticated user's addresses
- Update address
- Reject access to another user's address
- Authenticated order creation
- Reject order creation without authentication
- Reject order creation with empty items
- Reject order creation with another user's address
- Retrieve order by ID
- Reject access to another user's order
- List authenticated user's orders
- Filter orders by status
- Cancel `PENDING` order
- Reject cancellation of non-pending order
- Update order status
- Admin can list all orders
- Admin can filter all orders by status
- Customer cannot access all-orders report
- Background job updates pending orders to processing

Tests should use an isolated test database.

## 12. Documentation Requirements

### README.md

Should include:

- Project overview
- Tech stack
- Setup instructions
- Environment variables
- Migration commands
- Run server command
- Run test command
- API documentation URL

### REPO_MAP.md

Should include:

- Folder-by-folder explanation
- Key files and responsibilities

### AI_USAGE.md

Should include:

- Tools used, such as ChatGPT and Cursor AI
- What AI was used for
- Issues found during AI-assisted development
- Corrections made manually
- Final validation steps

Example AI usage statement:

```text
I used AI as a pair-programming assistant for requirement breakdown, project structure, initial API scaffolding, edge-case discovery, and test suggestions. I reviewed and corrected the generated output, especially around authentication, order ownership, status transitions, cancellation rules, total calculation, and background job testability.
```

## 13. Acceptance Criteria

The assignment is complete when:

- Users can register and login.
- Products/items are available for order creation.
- Authenticated users can manage saved addresses.
- Authenticated users can create orders with multiple items.
- Authenticated users can create orders using one of their saved addresses.
- Orders are persisted in the database.
- Order items preserve purchased product name and price.
- Orders preserve shipping address details at the time of order creation.
- Users can retrieve their own order details.
- Users can list their own orders.
- Admin users can list all orders across customers.
- Orders can be filtered by status.
- Order status can be updated.
- Pending orders can be cancelled.
- Non-pending orders cannot be cancelled.
- A scheduled job updates pending orders to processing every 5 minutes.
- Alembic migrations are included and working.
- Tests pass.
- README, REPO_MAP, and AI_USAGE documentation are included.

## 14. Interview Explanation

A strong explanation for the implementation:

```text
I designed the system around users, addresses, products, orders, and order items. The assignment requires orders with multiple items, so the `order_items` table is essential. Because the lifecycle includes shipped and delivered states, I added saved customer addresses and copied shipping address details onto each order at creation time.

I intentionally did not add a cart because the assignment focuses on order processing, not cart management. A customer can place one order with multiple items by sending an item array to the create-order endpoint.

I added JWT authentication so every address and order belongs to an authenticated customer. I kept API routes thin and placed business rules in the service layer, which allows both API endpoints and background jobs to reuse the same order processing logic.

For the scheduled processing requirement, I used Celery Beat with Redis. Beat publishes the pending-order processing task every 5 minutes, and a Celery worker executes it independently from the FastAPI web process. The actual job logic is isolated in a service function so it can be tested without waiting 5 minutes or requiring Redis in the test suite.

I used Alembic for migrations so schema changes are version-controlled and reproducible. I also added tests for authentication, address operations, order creation, filtering, cancellation rules, and background processing.
```
