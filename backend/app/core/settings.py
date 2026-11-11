from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"

    # Supabase
    supabase_url: str
    supabase_publishable_key: str
    supabase_secret_key: str

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

    # Email
    resend_api_key: str
    resend_from_email: EmailStr = "onboarding@resend.dev"
    invitation_encryption_key: str

    # AI providers
    ai_text_generation_provider: str = "openai"

    # OpenAI
    openai_api_key: str | None = None
    openai_text_generation_model: str = "gpt-4.1-mini"

    # Capability-specific models
    ai_message_explanation_model: str | None = None
    ai_task_assistance_model: str | None = None
    ai_conversation_title_model: str | None = None
    ai_request_classification_model: str | None = None
    ai_policy_generation_model: str | None = None

    # Knowledge retrieval (RAG)
    # "openai" for production; "local" is a deterministic, offline
    # hashing embedder intended for tests and development.
    ai_embedding_provider: str = "openai"
    openai_embedding_model: str = "text-embedding-3-small"
    knowledge_retrieval_top_k: int = 4
    knowledge_min_relevance: float = 0.3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
