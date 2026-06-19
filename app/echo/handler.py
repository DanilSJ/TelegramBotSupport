from aiogram import Router, F
from aiogram.types import Message
from app.echo.crud import get_operators, update_user_connect_topic, create_user
from core.models import db_helper
from services.ai import AI
import random
from core.config import settings

router = Router()


@router.message(F.text)
async def echo(message: Message):
    async with db_helper.scoped_session_dependency() as session:
        user = await create_user(
            session, message.from_user.id, message.from_user.username
        )

        if len(message.text) < 8:
            return await message.answer("Вопрос должен быть от 8 символов!!")

        if user.connect_operator:
            return await message.bot.send_message(
                chat_id=settings.GROUP_ID_SUPPORT,
                text=message.text,
                message_thread_id=user.user_topic_id,
            )

        operator_phrases = [
            "позови оператора",
            "нужен человек",
            "соедините с менеджером",
        ]

        if message.text.lower() in operator_phrases:
            operators = await get_operators(session)

            if not operators:
                return await message.answer(
                    "К сожалению, сейчас нет свободных операторов. Пожалуйста, подождите или оставьте сообщение."
                )

            operator = random.choice(operators)

            try:
                topic = await message.bot.create_forum_topic(
                    chat_id=settings.GROUP_ID_SUPPORT,
                    name=f"Запрос от {message.from_user.full_name}",
                )

                await message.bot.send_message(
                    chat_id=settings.GROUP_ID_SUPPORT,
                    text=f"Новое сообщение от пользователя: {message.text}",
                    message_thread_id=topic.message_thread_id,
                )
                await update_user_connect_topic(
                    session, message.from_user.id, topic.message_thread_id
                )

                return await message.answer(
                    "Ваш запрос передан оператору. Ожидайте ответа!"
                )

            except Exception as e:
                print(f"Ошибка при отправке сообщения оператору: {e}")
                return await message.answer(
                    "Произошла ошибка при соединении с оператором. Попробуйте позже."
                )

        ai = AI(message.text)
        result = await ai.send()
        return await message.answer(result)
