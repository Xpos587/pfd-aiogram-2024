from secrets import token_urlsafe

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings as _BaseSettings
from pydantic_settings import SettingsConfigDict
from sqlalchemy import URL


class BaseSettings(_BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8"
    )


class PostgresSettings(BaseSettings, env_prefix="POSTGRES_"):
    host: str
    port: str
    db: str
    user: str
    password: SecretStr

    def build_dsn(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.db,
        )


class RedisSettings(BaseSettings, env_prefix="REDIS_"):
    host: str
    port: int
    db: str
    user: str
    password: SecretStr


class WebhookSettings(BaseSettings, env_prefix="WEBHOOK_"):
    use: bool
    reset: bool
    base_url: str
    path: str
    port: int
    host: str
    secret_token: SecretStr = Field(default_factory=token_urlsafe)

    def build_url(self) -> str:
        return f"{self.base_url}{self.path}"


class Settings(BaseSettings):
    bot_token: SecretStr
    drop_pending_updates: bool
    sqlalchemy_logging: bool

    admin_ids: str
    time_zone: str

    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    webhook: WebhookSettings = Field(default_factory=WebhookSettings)

    def get_admin_ids(self) -> list[int]:
        return [
            int(admin_id)
            for admin_id in self.admin_ids.split(",")
            if admin_id.isdigit()
        ]


settings = Settings()
