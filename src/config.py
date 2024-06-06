from pydantic_settings import BaseSettings
from aiogram.fsm.storage.redis import Redis


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    ADMIN_ID: int
    REDIS_HOST: str
    TOKEN: str

    @property
    def get_url_asyncpg(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"


settings = Settings()
redis = Redis(host=settings.REDIS_HOST)
