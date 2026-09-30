from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    FRONTEND_ORIGIN: str = "http://localhost:3000"
    DATABASE_URL: str = "postgresql+asyncpg://price_oracle:price_oracle@postgres:5432/price_oracle"
    REDIS_URL: str = "redis://redis:6379/0"
    DEFAULT_USER_ID: str = "00000000-0000-0000-0000-000000000001"
    SCRAPE_INTERVAL_MINUTES: int = 45


settings = Settings()
