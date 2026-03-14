from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.exc import UnknownHashError
from passlib.context import CryptContext

from app.settings import Settings

settings = Settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password, password_hash)
    except UnknownHashError:
        # Legacy fallback: in some environments old rows may contain plaintext
        # in the password_hash column. In that case, do a direct comparison.
        return password == password_hash


def is_password_hash_recognized(password_hash: str) -> bool:
    return pwd_context.identify(password_hash) is not None


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    expires = timedelta(minutes=expires_minutes or settings.jwt_access_token_minutes)
    expire_at = datetime.now(timezone.utc) + expires

    to_encode = {
        "sub": subject,
        "exp": expire_at,
    }
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
