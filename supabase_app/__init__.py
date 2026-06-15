from supabase import Client, create_client

from config import SUPABASE_KEY, SUPABASE_URL

sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
