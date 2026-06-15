import os

from dotenv import load_dotenv

load_dotenv()

ENV: str = os.environ.get("ENV", "prod")
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")
