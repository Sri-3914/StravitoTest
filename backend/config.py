import os
from functools import lru_cache


class Settings:
    """Application configuration loaded from environment variables."""

    ihub_api_key: str
    ihub_base_url: str
    use_mock_api: bool

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

            if missing:
                missing_env = ", ".join(missing)
                raise RuntimeError(
                    f"Missing required environment variables: {missing_env}. "
                    "Set them before running the service or enable mock mode via IHUB_USE_MOCK."
                )

        self.use_mock_api = use_mock
        self.ihub_api_key = api_key or ""
        self.ihub_base_url = (base_url or "").rstrip("/")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}

