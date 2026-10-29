
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:3b"

    # Local inference settings
    ollama_temperature: float = 0.0
    ollama_num_predict: int = 512
    ollama_num_ctx: int = 4096
    ollama_timeout: int = 180

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
