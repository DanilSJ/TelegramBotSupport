import asyncio
from aiogram import Dispatcher
from aiogram.exceptions import (
    TelegramNetworkError,
    TelegramAPIError,
    TelegramServerError,
    TelegramUnauthorizedError,
    TelegramNotFound,
    TelegramBadRequest,
)
from core.config import bot
from app import start_router, echo_router, admin_router
from core.models import db_helper

from services.clear_topic import delete_old_topics

dp = Dispatcher()


async def delete_old_topics_task():
    """Фоновая задача для удаления старых топиков каждый час"""
    while True:
        try:
            # Ждем 1 час перед выполнением
            await asyncio.sleep(3600)

            async with db_helper.scoped_session_dependency() as session:
                await delete_old_topics(session, days=3)
        except Exception as e:
            print(e)


async def main():
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(echo_router)

    # Запускаем фоновую задачу
    background_task = asyncio.create_task(delete_old_topics_task())

    try:
        # Запускаем polling бота
        await dp.start_polling(bot)
    finally:
        # Отменяем фоновую задачу при завершении
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    print("Starting...")

    try:
        asyncio.run(main())
    except TelegramNetworkError:
        print("No internet connection")
    except TelegramUnauthorizedError:
        print("No authorization token")
    except TelegramNotFound:
        print("No bot token")
    except TelegramServerError:
        print("No server connection")
    except TelegramBadRequest:
        print("Bad request")
    except TelegramAPIError:
        print("No API connection")
    except KeyboardInterrupt:
        print("Exit")
