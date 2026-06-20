import pathlib
from aiogram import Bot
from pydantic_settings import BaseSettings
from os import getenv
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    BOT_TOKEN: str = getenv("BOT_TOKEN")
    GROUP_ID_SUPPORT: int = getenv("GROUP_ID_SUPPORT")

    BASE_URL: str = getenv("BASE_URL")
    AI_TOKEN: str = getenv("AI_TOKEN")

    db_url: str = f"sqlite+aiosqlite:///{BASE_DIR}/db.sqlite3"
    DB_ECHO: bool = getenv("DB_ECHO", "False") == "True"
    DB_POOL_NULL: bool = getenv("DB_POOL_NULL", "False") == "True"


settings = Settings()
bot = Bot(token=settings.BOT_TOKEN)
