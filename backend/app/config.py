from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


VIETNAM_TIMEZONE = timezone(timedelta(hours=7))


def as_vietnam_time(value: datetime) -> datetime:
    if value.tzinfo is not None:
        value = value.astimezone(VIETNAM_TIMEZONE)
    return value.replace(tzinfo=None)


def vietnam_now() -> datetime:
    return datetime.now(VIETNAM_TIMEZONE).replace(tzinfo=None)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str = "smart_house"

    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_USER: str
    MQTT_PASSWORD: str

    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 480

    @property
    def database_url(self) -> str:
        password = quote_plus(self.DB_PASSWORD)
        return (
            f"mysql+pymysql://{self.DB_USER}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
