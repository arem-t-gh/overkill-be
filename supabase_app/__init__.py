from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client, Client

sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
