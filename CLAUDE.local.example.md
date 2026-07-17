# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Overkill-be is an async FastAPI backend (Python 3.11, SQLAlchemy 2.0 async, Postgres, Supabase for auth) loosely based on Netflix's Dispatch project layout and follows a feature-oriented pattern. Dependency/task management is via `uv` + `poe` (poethepoet).

It is overkill in a sense that it is designed to mirror production development practices including CI/CD, containerized environments, testability, and scalability to gain depth as a Python backend engineer.

## Commands

Everything is meant to run **inside the dev container**.

- `./build.sh` — builds the dev image, starts Postgres, runs `alembic upgrade head` once, then tears the stack down. Run this once before `./start.sh`, and again whenever migrations need to be applied fresh.
- `./start.sh` — `docker compose up -d`; runs API (hot reload, source mounted) + Postgres.
- `./stop.sh` — `docker compose down`.
- `./enter-container.sh` — shells into the running `api` container (`docker compose exec api bash`). Run linters, tests, and `poe` commands from here.
- Inside the container:
  - `ruff format` / `ruff check` / `ruff check --fix` — linting/formatting.
  - `pytest` / `pytest path/to/test_file.py::TestClass::test_name` — run tests (pytest-asyncio, `asyncio_mode = "auto"`, so async tests need no `@pytest.mark.asyncio` decorator, though existing tests are inconsistent about including it).
  - `poe fresh-seed` — runs `db/seeders/seeder.py` (currently just seeds roles, idempotently via `session.merge`).
  - `poe manage-superuser <create-user-record|delete-user-record> <external_auth_id>` — CLI (`utils/cli/manage_superuser.py`, built with `cyclopts`) to create/delete a superuser DB row for an existing Supabase Auth UID. Also runnable in prod via the "Manage superuser" GitHub Action (`.github/workflows/manage_superuser_cli.yaml`, `main` branch only).
- Alembic: `alembic revision --autogenerate -m "message"` then `alembic upgrade head`. New SQLAlchemy models **must** be imported into `db/alembic_models/__init__.py` so that `alembic/env.py` can grab the `Base.metadata`.

CI mirrors this: `.github/workflows/pytest.yaml` runs `uv run pytest`, `.github/workflows/ruff.yaml` runs `ruff check` + `ruff format --check --diff`, on every push/PR.

## Architecture

### Request flow

`main.py` wires together three independent pieces at import time:
- `app.py` — the bare `FastAPI()` instance (also imports `db.alembic_models` so all ORM models are registered before anything else runs).
- `api/router_handler.py` — mounts the versioned API router (`api/v1/router.py`) at `/api/v1`, plus the root `/` health check (used by Railway's health check).
- `exception_handlers.py` — global handlers for Supabase `AuthApiError` and SQLAlchemy `DBAPIError`.

Versioned routers live under `api/v1/<domain>/` (`views.py` for routes, `schemas.py` for request/response Pydantic models specific to the HTTP layer). Views are kept thin — they resolve dependencies (`DBSession`, `SBClient`, current user) and delegate to the corresponding top-level domain module's `service.py`.

### Domain module pattern

Each business domain is a top-level package (`user/`, `role/`, `auth/`) containing:
- If necessary, a variation of a main file with a naming that makes sense for the domain/feature (e.g. for `db/database.py`, `auth/service.py`, `api/router_handler.py`) that contains major entities such as (not limited to) annotated dependencies, annotated factories, register functions.
- `models.py` — the SQLAlchemy ORM class **and** its related Pydantic read/update schemas in the same file (e.g. `user/models.py` has `User` ORM plus `UserReadBase`/`NewUserRead`/`UserRead`/`UserUpdate`). Pydantic models use `from_attributes=True` to validate directly off ORM instances.
- `service.py` — async business logic functions taking `DBSession`/`SBClient` as explicit parameters (not classes/repositories).
- `constants.py` (where relevant) — e.g. `role/constants.py` defines the fixed role IDs (`SUPERUSER_ROLE_ID=1`, `ADMIN_ROLE_ID=2`, `USER_ROLE_ID=3`) used for authorization checks and seeding.

`auth/` is the **internal** authorization layer (bearer token parsing, `get_current_user`, the `AuthorizedCurrentUser([role_ids])` dependency factory for role-gating routes) — distinct from `supabase_app/`, which is a thin wrapper around the actual Supabase Python client (sign up/in, fetch user by token, delete user). `auth/service.py` calls into `supabase_app/auth/service.py` for the external-provider calls, then reconciles/creates the local `User` row (a Supabase Auth account and a local `User` row are not guaranteed to be created atomically — both sign-up and sign-in flows lazily create the local row if it's missing).

### Database layer

`db/database.py` lazily initializes a singleton async engine and `async_sessionmaker` (important for test-friendliness — importing the module doesn't open connections). `DBSession = Annotated[AsyncSession, Depends(get_db_session)]` is the FastAPI dependency type used everywhere instead of importing `AsyncSession` directly. The session dependency does **not** auto-commit — commits happen explicitly in `service.py` functions; only rollback-on-exception is automatic. Similarly `SBClient` (`supabase_app/__init__.py`) is the equivalent dependency-injected type for the Supabase async client.

### Docker / deployment split

- Deployment (Railway): `Dockerfile` + `entrypoint.sh` (runs `alembic upgrade head`, `poe fresh-seed`, then `uvicorn` without reload).
- Local dev: `docker-compose.yaml` + `Dockerfile.local` + `entrypoint.local.sh` (uvicorn with `--reload`, source bind-mounted, Postgres container included). Railway does not use docker-compose, so anything compose-only stays local-only.
- See `docs/docker-implementation-pattern.md` and `docs/railway-setup.md` for the reasoning and Railway env var / GitHub environment setup.

### Notes

- `DB_URI`/`TEST_DB_URI` must use the `postgresql+asyncpg://` scheme (async driver) — easy to miss when copying a plain `postgresql://` URL from a provider.
