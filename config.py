import os

from dotenv import load_dotenv

from logging_config import setup_logging

load_dotenv()

ENV: str = os.environ.get("ENV", "prod")

# LOGGING
_DEBUG_BY_DEFAULT_ENVS = {"local", "dev", "stage"}
LOG_LEVEL: str = os.environ.get(
    "LOG_LEVEL", "DEBUG" if ENV in _DEBUG_BY_DEFAULT_ENVS else "INFO"
)

# Every module that needs config (which is effectively every module in this
# project, transitively) imports from here, so calling this as an import-time
# side effect -- same pattern as `load_dotenv()` above -- guarantees logging
# is configured before any `logging.getLogger(__name__)` call site anywhere
# in the app, seeders, CLI tools, or tests runs. See `logging_config.py`.
setup_logging(env=ENV, level=LOG_LEVEL)

# SUPABASE
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")

# DB
DB_URI: str = os.environ.get("DB_URI", "")
TEST_DB_URI: str = os.environ.get("TEST_DB_URI", "")
