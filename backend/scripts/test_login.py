from app.core.settings import settings
from app.services.supabase import create_public_supabase_client


client = create_public_supabase_client()

response = client.auth.sign_in_with_password(
    {
        "email": settings.test_user_email,
        "password": settings.test_user_password,
    }
)

print(response.session.access_token)