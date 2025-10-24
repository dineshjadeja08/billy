# Hotel Billing API

Comprehensive Django REST Framework backend for hotel billing, folio management, invoicing, payments, and daily reporting. The project exposes a fully documented REST API with JWT authentication and Swagger UI via drf-spectacular.

## Features

- JWT-based authentication with token refresh (SimpleJWT).
- CRUD APIs for guests, reservations, folios, and folio items.
- Invoice generation with automatic line capture, credit/debit notes, and PDF export.
- Payment capture, refund handling, and corporate account tracking.
- Configuration endpoints for taxes, payment methods, discounts, and corporate rates.
- Daily revenue, tax summary, and outstanding balance reports.
- Webhook receivers for PMS, POS, and Payment Gateway integrations.
- Interactive API docs available via Swagger UI and ReDoc.

## Tech Stack

- **Python** 3.13
- **Django** 5 with **Django REST Framework**
- **JWT Auth** via `djangorestframework-simplejwt`
- API schema with **drf-spectacular** and Swagger UI
- **ReportLab** for PDF invoice rendering
- **psycopg**; defaults to SQLite for local development

## Getting Started

```powershell
# install dependencies
C:/Users/RDJ/Desktop/Billy/.venv/Scripts/python.exe -m pip install -r requirements.txt

# apply migrations
C:/Users/RDJ/Desktop/Billy/.venv/Scripts/python.exe manage.py migrate

# create an admin user (follow prompts)
C:/Users/RDJ/Desktop/Billy/.venv/Scripts/python.exe manage.py createsuperuser

# run the development server
C:/Users/RDJ/Desktop/Billy/.venv/Scripts/python.exe manage.py runserver
```

Once the server is running:

- Swagger UI: http://127.0.0.1:8000/api/docs/
- ReDoc: http://127.0.0.1:8000/api/redoc/
- OpenAPI schema: http://127.0.0.1:8000/api/schema/

Use `POST /api/auth/login` with your credentials to obtain access and refresh tokens. Supply the access token in the `Authorization: Bearer <token>` header for authenticated endpoints. Superusers can manage users via `/api/users`.

## Running Tests

```powershell
C:/Users/RDJ/Desktop/Billy/.venv/Scripts/python.exe manage.py test
```

The test suite runs an end-to-end flow covering guest registration, folio creation, invoice generation, payment capture, reporting, and webhook ingestion.

## Project Structure

- `accounts/` – User management serializers and admin-only APIs.
- `billing/` – Domain models, serializers, viewsets, reports, and webhook endpoints.
- `hotel_billing/` – Project settings, URL routing, and schema wiring.

## Next Steps

- Swap SQLite for PostgreSQL/MySQL by updating `DATABASES` in `hotel_billing/settings.py`.
- Extend webhook handlers to process and persist external events.
- Add more granular permissions/roles and audit logging as needed.
