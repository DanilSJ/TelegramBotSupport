from aiogram import Bot
from pydantic_settings import BaseSettings
from os import getenv
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    BOT_TOKEN: str = getenv("BOT_TOKEN")
    GROUP_ID_SUPPORT: int = getenv("GROUP_ID_SUPPORT")

    BASE_URL: str = getenv("BASE_URL")
    AI_TOKEN: str = getenv("AI_TOKEN")

    DB_ECHO: bool = getenv("DB_ECHO", "False") == "True"
    DB_POOL_NULL = getenv("DB_POOL_NULL", "False") == "True"


settings = Settings()
bot = Bot(token=settings.BOT_TOKEN)
