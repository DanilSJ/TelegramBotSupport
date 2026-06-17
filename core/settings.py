from pydantic_settings import BaseSettings
from os import getenv
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    BOT_TOKEN: str = getenv("BOT_TOKEN")

    BASE_URL: str = getenv("BASE_URL")
    AI_TOKEN: str = getenv("AI_TOKEN")


settings = Settings()
