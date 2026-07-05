
### Notes
- You wont be using SQLAlchemy's create_all() stuff. Alembic will handle everything._
- Do this before setting up container so that `alembic upgrade head` execution upon build runs successfully.


### Steps
1. Create main database in db provider 
    - e.g. `postgresql+asyncpg://postgres:postgres@localhost/actualdb` 
    - Create the `actualdb` in **postgres** so that migrations have a place to go
1. Create declarative base somewhere in the project
1. Generate `alembic/` and `alembic.ini`  w/ `alembic init -t async alembic` 
1. Within `alembic.ini`, remove `sqlalchemy.url` key
1. Within `alembic/env.py`, dynamically configure `sqlalchemy.url` (e.g. `config.set_main_option("sqlalchemy.url", str(DB_URI))`)
1. Import declarative base metadata inside `alembic/env.py` and set `target_metadata`
1. Create other tables inheriting declarative base
1. Create a dedicated models package and import all tables inside an `__init__.py` (less messy)
1. Import models package to `env.py` (this will allow alembic to read all metadata)
1. `alembic revision --autogenerate -m "first migration"`
1. Check revision script in `versions/`
1. `alembic upgrade head` to run first migration and create tables
