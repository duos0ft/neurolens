import base64
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.settings import settings


class InvitationDecryptionError(Exception):
    pass


class InvitationCryptoService:
    def __init__(self) -> None:
        self.key = base64.urlsafe_b64decode(settings.invitation_encryption_key + "==")

        if len(self.key) != 32:
            raise ValueError("Invitation encryption key must be 256 bits")

        self.cipher = AESGCM(self.key)

    def encrypt(
        self,
        token: str,
        invitation_id: str,
    ) -> str:
        nonce = secrets.token_bytes(12)

        ciphertext = self.cipher.encrypt(
            nonce,
            token.encode("utf-8"),
            invitation_id.encode("utf-8"),
        )

        return base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")

    def decrypt(
        self,
        encrypted_token: str,
        invitation_id: str,
    ) -> str:
        try:
            payload = base64.urlsafe_b64decode(encrypted_token)

            nonce = payload[:12]
            ciphertext = payload[12:]

            plaintext = self.cipher.decrypt(
                nonce,
                ciphertext,
                invitation_id.encode("utf-8"),
            )

            return plaintext.decode("utf-8")

        except (ValueError, UnicodeDecodeError) as error:
            raise InvitationDecryptionError("Unable to decrypt invitation token") from error

        except Exception as error:
            raise InvitationDecryptionError("Invitation token authentication failed") from error
