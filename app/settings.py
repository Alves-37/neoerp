from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/erpcrm"
    jwt_secret_key: str = "CHANGE_ME"
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 60 * 24

    upload_dir: str = "uploads"

    cors_allow_origins: list[str] = ["http://localhost:5173"]

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        if not v:
            return v

        url = v.strip()
        if url.startswith("postgres://"):
            url = "postgresql+psycopg2://" + url[len("postgres://") :]
        elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
            url = "postgresql+psycopg2://" + url[len("postgresql://") :]

        if url.startswith("postgresql+psycopg2://"):
            if "sslmode=" not in url and "localhost" not in url and "127.0.0.1" not in url:
                url = url + ("&" if "?" in url else "?") + "sslmode=require"

        return url
