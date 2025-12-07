from email.message import EmailMessage

import aiosmtplib

from src.auth.utils import encode_jwt, decode_jwt
from src.core.exceptions import InvalidTokenError


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
    await aiosmtplib.send(message, hostname="localhost", port=1025)


def generate_link_for_verification(token: str) -> str:
    # TODO: remove hardcode
    return f"http://0.0.0.0:8000/api/v1/auth/verify?token={token}"


def create_token_for_verification(email: str):
    return encode_jwt({"sub": email}, 3 * 60)


async def send_verification_email(
    email: str,
):
    token = create_token_for_verification(email)
    admin_email = "textcanvas@mail.ru"
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
