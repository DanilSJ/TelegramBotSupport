from pydantic_settings import BaseSettings
from os import getenv
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    BOT_TOKEN: str = getenv("BOT_TOKEN")

    BASE_URL: str = getenv("BASE_URL")
    AI_TOKEN: str = getenv("AI_TOKEN")

    DB_ECHO: bool = getenv("DB_ECHO", "False") == "True"
    DB_POOL_NULL = getenv("DB_POOL_NULL", "False") == "True"



settings = Settings()
