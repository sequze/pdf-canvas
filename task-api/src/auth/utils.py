import jwt
from jwt import DecodeError
from src.core.config import settings
import bcrypt
from datetime import datetime, UTC, timedelta

from src.core.exceptions import InvalidTokenError


def encode_jwt(
    payload: dict,
    expire_minutes: int,
    private_key: str = settings.auth.private_key_path.read_text(),
    algorithm: str = settings.auth.algorithm,
) -> str:
    to_encode = payload.copy()
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=expire_minutes)
    to_encode.update(
        iat=now,
        exp=expire,
    )
    encoded_jwt = jwt.encode(to_encode, private_key, algorithm=algorithm)
    return encoded_jwt


def decode_jwt(
    jwt_token: str | bytes,
    public_key: str = settings.auth.public_key_path.read_text(),
    algorithm: str = settings.auth.algorithm,
) -> dict:
    try:
        decoded_jwt = jwt.decode(
            jwt_token, public_key, algorithms=[algorithm], options={"verify_exp": False}
        )
    except DecodeError:
        raise InvalidTokenError("Error decoding jwt token")
    return decoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
