
# Introduction

Feature-oriented FastAPI backend app designed to mirror production development practices including CI/CD, containerized environments, Supabase authentication with custom RBAC, and automated database migrations.

Future implementations would introduce more AI integrations, solving scaling problems, distributed computing, and cloud/infra migrations via IaC.

_This repo is loosely based on: https://github.com/Netflix/dispatch_


## Pre reqs
- Python 3.11
- uv python package manager
- Docker
- Claude Code
- Docker desktop (container GUI)
- pgAdmin (Postgres GUI)


## Setup
- Create `.env` file
- `./build.sh` to create the container entities
- `./start.sh` to run the project
- `./stop.sh` to stop the proejct
- If you need to run scripts within the environment: `./enter-container.sh`

##

- API in [http://0.0.0.0:8000](http://0.0.0.0:8000)
- API documentation in [http://0.0.0.0:8000/docs](http://0.0.0.0:8000/docs)



##

### Seeding
- `./enter-container.sh`
- `poe fresh-seed`

### Running linters
- `./enter-container.sh`
- `ruff format`
- `ruff check`
- `ruff check --fix`

### Testing
- `./enter-container.sh`
- `pytest <args>`

##

### Running CLI tools
See `pyproject.toml`'s `[tool.poe.tasks*]` sections for `command`s
- `./enter-container.sh`
- `poe <command> <args>`



### Monitoring DB via pgadmin
- Register server
- Host name: `localhost`
    - *Within docker network, it's "db" (see also `docker-compose.yaml`). But through mapping, `localhost:5432` maps to `db:5432`*
- Set username and password based on .env
- Save


### Creating superuser
- Create a user in supabase auth
    - Copy UID
- Create user record
    - If local
        - Run `poe superuser create-user-record` 
    - If dev
        - Run `Manage superuser`'s `create-user-record` in Github action
- Check postgres if user record has been made

##

### Local logging

- You can manually `log` and access the logs in `logs/`

##

### Cloud deployment
- Currently deployed in Railway (See: `docs/railway-setup.md`)
    - Uses config-as-code
- This is intended to be deployed to AWS via CDK
