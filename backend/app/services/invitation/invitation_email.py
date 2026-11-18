from datetime import datetime
from urllib.parse import urlencode

from app.core.settings import settings
from app.schemas.email.resend import ResendSendEmailRequest
from app.services.email.template_renderer import EmailTemplateRenderer


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
        organization_name: str,
        expires_at: datetime,
    ) -> ResendSendEmailRequest:
        invitation_url = cls.build_invitation_url(token)

        context = {
            "recipient_email": recipient,
            "organization_name": organization_name,
            "invite_url": invitation_url,
            "expiry_date": expires_at.strftime("%d %B %Y"),
        }

        html = EmailTemplateRenderer.render(
            "invitation.mjml",
            **context,
        )

        text = EmailTemplateRenderer.render(
            "invitation.txt",
            **context,
        )

        return ResendSendEmailRequest(
            sender=settings.resend_from_email,
            to=[recipient],
            subject=f"Join {organization_name} on NeuroLens",
            html=html,
            text=text,
        )
