_This repo is loosely based on: https://github.com/Netflix/dispatch_

<!-- - `poetry install`
- `poetry env use 3.12`
- mac: `eval $(poetry env activate)`
- `fastapi dev main.py` -->
<!-- SHOULD BE USING DOCKER INSTEAD -->

<!-- TODO: ALL COMMANDS SHOULD BE RUNNING INSIDE DOCKER (cli, linters, etc) -->

### Pre reqs
- Python 3.11
- uv package manager

### Enter venv
macOS/Linux
- `source .venv/bin/activate`

### Running CLI tools
See `pyproject.toml`'s `[tool.poe.tasks*]` sections for `command`s
- Enter venv
- `poe <command> <args>`

### Running linters
- Enter venv
- `ruff format`
- `ruff check`
- `ruff check --fix`



### Create database 
1. `cli command to automatically create database instead of manually creating it`
2. `alembic upgrade head`