import html
from urllib.parse import urlencode

from app.core.settings import settings
from app.schemas.resend import ResendSendEmailRequest


class InvitationEmailService:
    @staticmethod
    def build_invitation_url(token: str) -> str:
        query = urlencode({"token": token})

        return f"{settings.frontend_url.rstrip('/')}/auth/accept-invite?{query}"

    @classmethod
    def build_email(
        cls,
        recipient: str,
        token: str,
    ) -> ResendSendEmailRequest:
        invitation_url = cls.build_invitation_url(token)

        safe_url = html.escape(
            invitation_url,
            quote=True,
        )

        return ResendSendEmailRequest(
            sender=settings.resend_from_email,
            to=[recipient],
            subject="You're invited to NeuroLens",
            html=f"""
            <!DOCTYPE html>
            <html lang="en">
              <body style="font-family: Arial, sans-serif;">
                <h2>You're invited to NeuroLens</h2>
                <p>
                  You've been invited to join NeuroLens.
                </p>
                <p>
                  <a href="{safe_url}">
                    Accept your invitation
                  </a>
                </p>
                <p>
                  This invitation link is private.
                  Do not share it with anyone.
                </p>
              </body>
            </html>
            """,
        )
