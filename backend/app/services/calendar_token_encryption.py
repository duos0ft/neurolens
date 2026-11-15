from cryptography.fernet import Fernet, InvalidToken

from app.core.settings import settings


class CalendarTokenEncryptionError(Exception):
    pass


class CalendarTokenEncryption:
    def __init__(self) -> None:
        key = settings.google_calendar_token_encryption_key

        if not key:
            raise CalendarTokenEncryptionError("Calendar token encryption is not configured")

        try:
            self.fernet = Fernet(key.encode("utf-8"))
        except (ValueError, TypeError) as error:
            raise CalendarTokenEncryptionError("Invalid calendar token encryption key") from error

    def encrypt(self, token: str) -> bytes:
        if not token:
            raise CalendarTokenEncryptionError("Cannot encrypt an empty token")

        return self.fernet.encrypt(token.encode("utf-8"))

    def decrypt(self, encrypted_token: bytes) -> str:
        try:
            return self.fernet.decrypt(encrypted_token).decode("utf-8")
        except (InvalidToken, ValueError, TypeError) as error:
            raise CalendarTokenEncryptionError("Unable to decrypt calendar token") from error
