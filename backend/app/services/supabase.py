from supabase import Client, create_client

from app.core.settings import settings


def create_public_supabase_client() -> Client:
    return create_client(
        settings.supabase_url,
        settings.supabase_publishable_key,
    )


def create_authenticated_supabase_client(access_token: str) -> Client:
    client = create_public_supabase_client()
    client.postgrest.auth(access_token)
    return client