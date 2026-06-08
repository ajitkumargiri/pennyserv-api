# PennyServ API

Production-ready FastAPI foundation for PennyServ, an AI-powered grocery savings and price intelligence platform.

This repository focuses on API foundation, clean architecture boundaries, and customer-facing workflows built on normalized upstream grocery intelligence from SaveBasket data-platform.

## Architecture

- Architectural style: Clean Architecture + Domain-Driven Design (DDD).
- Bounded contexts: `catalog`, `pricing`, `offers`, `search`, `receipts`, `basket`, `users`, `auth`, `normalization_quality`.
- Platform modules: `caching`, `jobs`, `observability`, `integrations/data_platform`.
- Layering per context:
  - `domain`: entities, value objects, repository contracts.
  - `application`: use-case orchestration services.
  - `infrastructure`: persistence and external integrations.
  - `presentation`: API adapters and routers.

Boundary documentation: `docs/data-platform-boundary.md`.

## Project Structure

```text
.
├── alembic/
├── src/
│   ├── core/
│   ├── shared/
│   ├── integrations/data_platform/
│   ├── catalog/
│   ├── pricing/
│   ├── offers/
│   ├── normalization_quality/
│   ├── search/
│   ├── receipts/
│   ├── basket/
│   ├── users/
│   ├── auth/
│   ├── caching/
│   ├── jobs/
│   ├── observability/
│   ├── shared/
│   └── main.py
├── docs/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── railway.toml
└── pyproject.toml
```

## Dependency Management (`uv`)

- Python runtime: `3.13.x`
- Package manager and environment workflow: `uv`
- Core dependencies:
	- `fastapi`, `uvicorn[standard]`
	- `sqlalchemy` async, `asyncpg`, `alembic`, `psycopg[binary]`
	- `pydantic`, `pydantic-settings`
	- `openai`
	- `pgvector`
	- `redis`
	- `python-json-logger`
- Dev dependencies:
	- `pytest`, `pytest-cov`, `httpx`, `ruff`, `mypy`

Install and run locally:

```bash
uv sync --dev
uv run uvicorn src.main:app --reload
```

## Environment Strategy

- Configuration source of truth: environment variables.
- Local development: `.env` (template in `.env.example`).
- Typed settings loaded via `pydantic-settings` in `src/core/config.py`.
- Environment modes: `local`, `staging`, `production`.
- Strict validation for staging/production required values.
- API docs are disabled automatically in `production` mode.

## Logging Strategy

- Centralized logging configuration in `src/core/logging.py`.
- Structured JSON log format for production parsing.
- Per-request correlation via `X-Request-ID` middleware.
- Request ID is attached to every log record for traceability.

## Exception Handling Strategy

- Global exception registration in `src/core/exceptions.py`.
- Typed domain exceptions in `src/shared/domain/exceptions.py`.
- Standardized error response envelope:
	- `error.code`
	- `error.message`
	- optional `error.details`
- Handles domain, validation, database, and unexpected runtime errors.

## Health and OpenAPI

- Health endpoints:
	- `GET /health/live`
	- `GET /health/ready`
- Versioned API root: `/api/v1`
- OpenAPI docs endpoints configured by environment:
	- `/openapi.json`
	- `/docs` (non-production)
	- `/redoc` (non-production)

## Database and Migrations

- Database target: PostgreSQL (Supabase-compatible).
- ORM: SQLAlchemy 2.0 async (`src/core/db`).
- Migration tool: Alembic (`alembic/`).
- `pgvector` extension bootstrap included in Alembic environment.

Run migrations:

```bash
uv run alembic upgrade head
```

## Container and Deployment Baseline

- Docker runtime: `Dockerfile` (Python 3.13 + `uv`).
- Local stack: `docker-compose.yml` with:
	- API service
	- PostgreSQL + pgvector service
	- Redis service
- Railway deployment: `railway.toml` with Docker build and `/health/live` check.

## Tests

- Test framework: `pytest`
- Baseline tests include:
	- app startup assertions
	- liveness and readiness endpoints
	- OpenAPI document availability

Run tests:

```bash
uv run pytest
```