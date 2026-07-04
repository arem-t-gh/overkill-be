#!/bin/sh
set -e

alembic upgrade head

poe fresh-seed

exec uvicorn main:app --host 0.0.0.0 --port 8000