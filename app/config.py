from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Receptionist MVP"
    app_env: str = "local"
    log_level: str = "INFO"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"

    vapi_api_key: str | None = None
    vapi_webhook_secret: str | None = None

    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_phone_number: str | None = None

    google_calendar_id: str | None = None
    google_application_credentials: str | None = None

    business_timezone: str = "America/New_York"
    business_name: str = "Example Business"
    business_phone: str = Field(default="+15555550100")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
