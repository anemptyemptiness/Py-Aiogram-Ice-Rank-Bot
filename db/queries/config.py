from dataclasses import dataclass
from environs import Env


@dataclass
class Settings:
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    @property
    def get_url_asyncpg(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


env = Env()
env.read_env()

settings = Settings(
    DB_HOST=env("host"),
    DB_PORT=env("port"),
    DB_USER=env("user"),
    DB_PASS=env("password"),
    DB_NAME=env("database"),
)
