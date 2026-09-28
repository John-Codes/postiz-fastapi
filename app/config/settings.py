from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Official Postiz public API is mounted at /api/public/v1 behind the bundled
# nginx, on the host port the official compose maps (4007 here).
DEFAULT_POSTIZ_API_URL = "http://127.0.0.1:4007/api/public/v1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postiz_api_url: str = DEFAULT_POSTIZ_API_URL
    postiz_api_key: str = ""
    postiz_timeout_seconds: float = 10.0

    fastapi_host: str = "127.0.0.1"
    fastapi_port: int = 8000

    @property
    def is_postiz_configured(self) -> bool:
        """Health must work without Postiz, so callers check this before using the API."""
        return bool(self.postiz_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
