from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"

    # Supabase
    supabase_url: str
    supabase_publishable_key: str
    supabase_secret_key: str
    supabase_policy_bucket: str = "company-policies"

    # PostgreSQL
    database_url: str
    migration_database_url: str | None = None

    # Auth0
    auth0_domain: str
    auth0_client_id: str
    auth0_client_secret: str
    auth0_redirect_uri: str
    auth0_management_client_id: str
    auth0_management_client_secret: str

    # Frontend
    frontend_url: str = "http://localhost:3000"

    # Sessions
    session_cookie_name: str = "neurolens_session"
    session_lifetime_seconds: int = 604800  # 7 days
    session_cookie_secure: bool = True
    csrf_secret_key: str

    # OAuth
    oauth_state_lifetime_seconds: int = 600  # 10 minutes
    invitation_lifetime_days: int = 7
    invitation_provisioning_lease_seconds: int = 300

    # Google Calendar
    google_calendar_client_id: str | None = None
    google_calendar_client_secret: str | None = None
    google_calendar_redirect_uri: str = (
        "http://localhost:8000/api/integrations/google-calendar/callback"
    )
    google_calendar_scopes: str = "https://www.googleapis.com/auth/calendar.events"
    google_calendar_token_encryption_key: str | None = None

    # Email
    resend_api_key: str
    resend_from_email: EmailStr = "onboarding@resend.dev"
    invitation_encryption_key: str

    # AI providers
    ai_text_generation_provider: str = "openai"
    ai_embedding_provider: str = "openai"
    ai_sentiment_provider: str = "modernbert"

    # OpenAI
    openai_api_key: str | None = None
    openai_text_generation_model: str = "gpt-4.1-mini"

    # Capability-specific models
    ai_message_explanation_model: str | None = None
    ai_task_assistance_model: str | None = None
    ai_conversation_title_model: str | None = None
    ai_request_classification_model: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    ai_embedding_dimensions: int = 1536

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
