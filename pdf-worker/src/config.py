from pathlib import Path

from shared import RedisConfig, BrokerConfig
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


class MarkdownConfig(BaseModel):
    # CSS files: "name": "path"
    css_files: dict[str, str] = {
        "default": BASE_DIR / "static/css/default.css",
        "github_dark": BASE_DIR / "static/css/github-dark.css",
    }


class AwsConfig(BaseModel):
    access_key: str
    secret_key: str
    endpoint_url: str
    bucket_name: str
    domain: str
    folder: str | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        extra="ignore",
        case_sensitive=False,
        env_nested_delimiter="__",
    )
    rmq: BrokerConfig
    md: MarkdownConfig = MarkdownConfig()
    redis: RedisConfig
    aws: AwsConfig


settings = Settings()
