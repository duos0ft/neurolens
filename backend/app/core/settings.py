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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
