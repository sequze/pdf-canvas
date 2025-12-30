from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from shared import RedisConfig, BrokerConfig

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


class PromptConfig(BaseModel):
    folder_path: str = "src/prompts/"
    prompt_name: str = "default.txt"

    @property
    def prompt_path(self) -> str:
        return f"{self.folder_path}/{self.prompt_name}"


class YandexGptLLMConfig(BaseModel):
    yandex_cloud_folder: str
    yandex_cloud_api_key: str
    yandex_cloud_model: str
    base_url: str
    temperature: float = 0.5

    @property
    def model(self) -> str:
        return f"gpt://{self.yandex_cloud_folder}/{self.yandex_cloud_model}"


class Settings(BaseSettings):
    llm: YandexGptLLMConfig
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        extra="ignore",
        case_sensitive=False,
        env_nested_delimiter="__",
    )
    llm_prompt: PromptConfig = PromptConfig()
    redis: RedisConfig
    rmq: BrokerConfig


settings = Settings()
