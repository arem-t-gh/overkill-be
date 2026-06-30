_This repo is loosely based on: https://github.com/Netflix/dispatch_

<!-- - `poetry install`
- `poetry env use 3.12`
- mac: `eval $(poetry env activate)`
- `fastapi dev main.py` -->
<!-- SHOULD BE USING DOCKER INSTEAD -->

<!-- TODO: ALL COMMANDS SHOULD BE RUNNING INSIDE DOCKER (cli, linters, etc) -->

## Setup
- `./build.sh` to create the container entities
- `./start.sh` to run the project
- `./stop.sh` to stop the proejct
- If you need to run scripts within the environment: `./enter-container.sh`

##

### Seeding
- Enter container
- `poe fresh-seed`

### Running linters
- Enter container
- `ruff format`
- `ruff check`
- `ruff check --fix`

### Testing
- Enter container
- `pytest <args>`

##

### Running CLI tools
See `pyproject.toml`'s `[tool.poe.tasks*]` sections for `command`s
- Enter container
- `poe <command> <args>`



### Monitoring DB via pgadmin
- Register server
- Host name: `localhost`
    - *Within docker network, it's "db" (see also `docker-compose.yaml`). But through mapping, `localhost:5432` maps to `db:5432`*
- Set username and password based on .env
- Save