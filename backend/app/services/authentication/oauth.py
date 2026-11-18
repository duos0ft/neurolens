import base64
import hashlib
import secrets


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def generate_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()

    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
