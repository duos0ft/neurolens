from fastapi_csrf_protect import CsrfProtect
from pydantic import BaseModel

from app.core.settings import settings


class CsrfSettings(BaseModel):
    secret_key: str = settings.csrf_secret_key
    cookie_key: str = "neurolens_csrf"
    cookie_path: str = "/"
    cookie_samesite: str = "lax"
    cookie_secure: bool = settings.session_cookie_secure
    cookie_httponly: bool = True
    token_key: str = "csrf_token"
    token_location: str = "header"
    header_name: str = "X-CSRF-Token"


def configure_csrf() -> None:
    CsrfProtect.load_config(lambda: CsrfSettings())
