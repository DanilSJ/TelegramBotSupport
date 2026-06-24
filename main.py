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

from services.clear_topic import delete_old_topics, check_and_delete_closed_topics

dp = Dispatcher()


async def delete_old_topics_task():
    """Фоновая задача для удаления старых топиков и закрытых топиков каждые 30 минут"""
    while True:
        try:
            # Ждем 30 минут перед выполнением
            await asyncio.sleep(1800)  # 30 минут

            async with db_helper.scoped_session_dependency() as session:
                # Удаляем старые топики (3 дня)
                deleted_old = await delete_old_topics(session, days=3)

                # Удаляем закрытые топики (через 30 минут)
                result = await check_and_delete_closed_topics(session)

                if deleted_old > 0 or result["deleted_closed"] > 0:
                    print(
                        f"Удалено старых топиков: {deleted_old}, закрытых топиков: {result['deleted_closed']}"
                    )

        except Exception as e:
            print(f"Ошибка в фоновой задаче: {e}")


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
