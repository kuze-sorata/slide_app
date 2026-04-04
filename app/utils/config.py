import shutil
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Slide Draft Generator"
    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4.1-mini", alias="LLM_MODEL")
    llm_base_url: str = Field(default="https://api.openai.com/v1", alias="LLM_BASE_URL")
    llm_timeout_ms: int = Field(default=60000, alias="LLM_TIMEOUT_MS")
    llm_max_retries: int = Field(default=2, alias="LLM_MAX_RETRIES")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    gemini_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai",
        alias="GEMINI_BASE_URL",
    )
    ollama_base_url: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="phi3:mini", alias="OLLAMA_MODEL")
    ollama_connect_timeout: float = Field(default=10.0, alias="OLLAMA_CONNECT_TIMEOUT")
    ollama_read_timeout: float = Field(default=120.0, alias="OLLAMA_READ_TIMEOUT")
    ollama_write_timeout: float = Field(default=30.0, alias="OLLAMA_WRITE_TIMEOUT")
    ollama_pool_timeout: float = Field(default=10.0, alias="OLLAMA_POOL_TIMEOUT")
    lmstudio_base_url: str = Field(default="http://localhost:1234", alias="LMSTUDIO_BASE_URL")
    lmstudio_model: str = Field(default="local-model", alias="LMSTUDIO_MODEL")
    mock_generation: bool = Field(default=False, alias="MOCK_GENERATION")
    llm_timeout_seconds: float = Field(default=120.0, alias="LLM_TIMEOUT_SECONDS")
    generation_timeout_seconds: float = Field(default=120.0, alias="GENERATION_TIMEOUT_SECONDS")
    marp_cli_path: str = Field(default="marp", alias="MARP_CLI_PATH")
    marp_theme: str = Field(default="default", alias="MARP_THEME")
    chrome_path: str | None = Field(default=None, alias="CHROME_PATH")
    marp_timeout_seconds: float = Field(default=60.0, alias="MARP_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    @property
    def resolved_marp_cli_path(self) -> str:
        if self.marp_cli_path and self.marp_cli_path != "/path/to/marp":
            return self.marp_cli_path

        detected = shutil.which("marp")
        if detected:
            return detected

        candidate = Path("/home/sora/.nvm/versions/node/v22.22.2/bin/marp")
        if candidate.exists():
            return str(candidate)

        return self.marp_cli_path

    @property
    def resolved_chrome_path(self) -> str | None:
        if self.chrome_path and self.chrome_path != "/path/to/chrome-headless-shell":
            return self.chrome_path

        for binary_name in (
            "chrome-headless-shell",
            "google-chrome",
            "chromium",
            "chromium-browser",
            "chrome",
        ):
            detected = shutil.which(binary_name)
            if detected:
                return detected

        return self.chrome_path


@lru_cache
def get_settings() -> Settings:
    return Settings()
