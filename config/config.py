from dataclasses import dataclass
from aiogram.fsm.storage.redis import Redis
from environs import Env


@dataclass
class TgBot:
    token: str


@dataclass
class Config:
    tg_bot: TgBot
    redis: Redis
    user_db: str
    password_db: str
    database: str
    host_db: str
    admin: int


def load_config() -> Config:
    env = Env()
    env.read_env()

    return Config(tg_bot=TgBot(token=env("TOKEN")),
                  redis=Redis(host=f"{env('redis_host')}"),
                  user_db=env("user"),
                  password_db=env("password"),
                  database=env("database"),
                  host_db=env("host"),
                  admin=int(env("admin")),)


config: Config = load_config()
