import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


class Settings:
    """Application configuration loaded from environment variables."""

    ihub_api_key: str
    ihub_base_url: str
    use_mock_api: bool
    azure_openai_endpoint: Optional[str]
    azure_openai_api_key: Optional[str]
    azure_openai_deployment: Optional[str]
    azure_openai_api_version: str
    enable_azure_llm: bool

    stravito_poll_max_retries: int
    stravito_poll_interval: float

    def __init__(self) -> None:
        missing = []
        use_mock = _to_bool(os.getenv("IHUB_USE_MOCK", "false"))

        api_key = os.getenv("IHUB_API_KEY")
        base_url = os.getenv("IHUB_BASE_URL")

        if not use_mock:
            if not api_key:
                missing.append("IHUB_API_KEY")
            if not base_url:
                missing.append("IHUB_BASE_URL")

        azure_enabled = _to_bool(os.getenv("AZURE_OPENAI_ENABLED", "true"))
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")

        if azure_enabled:
            if not azure_endpoint:
                missing.append("AZURE_OPENAI_ENDPOINT")
            if not azure_api_key:
                missing.append("AZURE_OPENAI_API_KEY")
            if not azure_deployment:
                missing.append("AZURE_OPENAI_DEPLOYMENT")

        if missing:
            missing_env = ", ".join(missing)
            raise RuntimeError(
                f"Missing required environment variables: {missing_env}. "
                "Set them before running the service or toggle AZURE_OPENAI_ENABLED / IHUB_USE_MOCK as needed."
            )

        self.use_mock_api = use_mock
        self.ihub_api_key = api_key or ""
        self.ihub_base_url = (base_url or "").rstrip("/")

        self.enable_azure_llm = azure_enabled
        self.azure_openai_endpoint = azure_endpoint
        self.azure_openai_api_key = azure_api_key
        self.azure_openai_deployment = azure_deployment
        self.azure_openai_api_version = azure_api_version
        self.stravito_poll_max_retries = int(
            os.getenv("STRAVITO_POLL_MAX_RETRIES", "60")
        )
        self.stravito_poll_interval = float(os.getenv("STRAVITO_POLL_INTERVAL", "2"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}

