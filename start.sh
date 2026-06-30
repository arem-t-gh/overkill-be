#!/bin/sh
set -e

# Starts the API and Postgres locally with hot reload.
# Your source code is mounted into the container, so edits reflect immediately.

docker compose up -d