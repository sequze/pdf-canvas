from email.message import EmailMessage

import aiosmtplib
import logging

from src.auth.utils import encode_jwt, decode_jwt
from src.core.exceptions import InvalidTokenError
from src.core.config import settings
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


async def send_email(
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
):
    message = EmailMessage()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    try:
        await aiosmtplib.send(
            message,
            hostname=settings.email.smtp_host,
            port=settings.email.smtp_port,
            username=settings.email.smtp_user,
            password=settings.email.smtp_password,
            start_tls=settings.email.smtp_start_tls,
            use_tls=settings.email.smtp_use_tls,
        )
        logger.info("Verification email sent to %s", to_email)
    except Exception as e:
        # log exception details for diagnostics and re-raise so caller can handle it
        logger.exception("Failed to send verification email to %s: %s", to_email, e)
        raise


def generate_link_for_verification(token: str) -> str:
    # use verification base url from settings
    qs = urlencode({"token": token})
    return f"{settings.email.verification_base_url}?{qs}"


def create_token_for_verification(email: str):
    return encode_jwt({"sub": email}, settings.email.verification_token_expire_minutes)


async def send_verification_email(
    email: str,
):
    token = create_token_for_verification(email)
    admin_email = settings.email.default_from
    await send_email(
        from_email=admin_email,
        to_email=email,
        subject="Registration Confirmation on TextCanvas",
        body=f"To confirm your registration, follow the link {generate_link_for_verification(token)}",
    )


def verify_verification_token(token: str):
    try:
        payload = decode_jwt(token)
        return payload
    except InvalidTokenError:
        return None
