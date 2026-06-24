from fastapi import FastAPI

# To register models in Python upon running and prevent missing references error
from db import alembic_models  # noqa

app = FastAPI(title="Overkill")
