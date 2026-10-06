from supabase import Client, create_client

from app.core.settings import settings


def create_supabase_client() -> Client:
    return create_client(
        settings.supabase_url,
        settings.supabase_publishable_key,
    )


supabase = create_supabase_client()