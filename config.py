import os

from dotenv import load_dotenv

load_dotenv()

ENV: str = os.environ.get("ENV", "prod")

# SUPABASE
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")

# DB
DB_URI: str = os.environ.get("DB_URI", "")
