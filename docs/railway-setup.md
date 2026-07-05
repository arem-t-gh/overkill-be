## Postgres db
- Create Postgres service
- Copy
    - POSTGRES_USER
    - POSTGRES_PASSWORD 
    - POSTGRES_DB 
    - DATABASE_URL
        - replace `postgresql://` prefix to `postgresql+asyncpg://`
    - DATABASE_PUBLIC_URL
        - replace `postgresql://` prefix to `postgresql+asyncpg://`
- Adjust settings if necessary

## Backend api
- Create github repository service
- Go to `Variables` tab and update values (should auto-suggest based on `.env.example`)
    - Don't forget `Supabase` env vars
- Go to github repository
    - Settings tab
    - Environments section
        - Railway should add the service's environment (e.g. `overkill-be / dev` matching the environment from Railway)
    - Add environment secret `DB_URI` value of `DATABASE_PUBLIC_URL`
- Go back to railway api service and deploy
- Go to Settings tab
    - Networking section
    - Public networking
        - Generate domain
        - Enter port
        - Generate domain

# Checks
- API service settings should take its configurations from `railway.json`
- Be able to open the public domain
- Postgres database should be seeded with table and rows
- Should be able to successfully run github workflows (e.g. `Manage superuser: create-user-record`) against the app
