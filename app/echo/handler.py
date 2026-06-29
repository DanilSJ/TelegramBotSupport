import asyncio
from typing import List, Dict

from aiogram import Router
from aiogram.types import Message
from app.echo.crud import (
    update_user_connect_topic,
    create_user,
    create_topic,
    create_message,
    get_user_messages,
    get_topics,
    get_user,
    get_phrases,
    update_user_disconnect_topic,
    close_dialog,
    get_topic,
    get_user_ai_messages,
)
from core.models import db_helper
from services.ai import AI
from core.config import settings
from services.crud import get_ai_use

router = Router()


async def get_user_history_messages(
    session, user_id: int, limit: int = 30
) -> List[Dict[str, str]]:
    messages = await get_user_ai_messages(session, user_id, limit=limit)

    history_messages: List[Dict[str, str]] = []

    for msg in messages:
        history_messages.append({"role": "user", "content": msg.message})

        if msg.ai_message:
            history_messages.append({"role": "assistant", "content": msg.ai_message})

    return history_messages


@router.message()
async def echo(message: Message):
    async with db_helper.scoped_session_dependency() as session:
        user = await create_user(
            session, message.from_user.id, message.from_user.username
        )

        if user.is_block:
            return None

        # Operator send message
        if user.is_operator:
            topics = await get_topics(session)
            for el in topics:
                if message.text and message.text == "/closed":
                    await close_dialog(session, el.id)
                    return await message.answer("Диалог закрыт")
                if message.message_thread_id == el.topic_id:
                    client_user = await get_user(session, el.user_id)
                    if message.text:
                        await create_message(
                            session=session,
                            user_id=user.id,
                            id_message=message.message_id,
                            message=message.text,
                            topic_id=user.user_topic_id,
                            is_admin=True,
                        )
                    try:
                        if message.text:
                            return await message.bot.send_message(
                                client_user.telegram_id,
                                message.text,
                            )
                        elif message.photo:
                            return await message.bot.send_photo(
                                client_user.telegram_id,
                                photo=message.photo[-1].file_id,
                                caption=message.caption,
                            )
                        elif message.video:
                            return await message.bot.send_video(
                                client_user.telegram_id,
                                video=message.video.file_id,
                                caption=message.caption,
                            )
                        elif message.audio:
                            return await message.bot.send_audio(
                                client_user.telegram_id,
                                audio=message.audio.file_id,
                                caption=message.caption,
                            )
                        elif message.document:
                            return await message.bot.send_document(
                                client_user.telegram_id,
                                document=message.document.file_id,
                                caption=message.caption,
                            )
                        elif message.sticker:
                            return await message.bot.send_sticker(
                                client_user.telegram_id,
                                sticker=message.sticker.file_id,
                            )
                        elif message.voice:
                            return await message.bot.send_voice(
                                client_user.telegram_id,
                                voice=message.voice.file_id,
                                caption=message.caption,
                            )
                        elif message.video_note:
                            return await message.bot.send_video_note(
                                client_user.telegram_id,
                                video_note=message.video_note.file_id,
                            )
                        elif message.animation:
                            return await message.bot.send_animation(
                                client_user.telegram_id,
                                animation=message.animation.file_id,
                                caption=message.caption,
                            )
                        elif message.poll:
                            return await message.bot.send_poll(
                                client_user.telegram_id,
                                question=message.poll.question,
                                options=[opt.text for opt in message.poll.options],
                                is_anonymous=message.poll.is_anonymous,
                                type=message.poll.type,
                                allows_multiple_answers=message.poll.allows_multiple_answers,
                            )
                        else:
                            return await message.bot.send_message(
                                client_user.telegram_id,
                                f"Неизвестный тип сообщения: {message.content_type}",
                            )

                    except Exception as err:
                        return await message.answer(
                            f"Произошла ошибка (Возможно человек заблокировал бота): {err}"
                        )

        if user.connect_operator:
            topic = await get_topic(session, user.user_topic_id)
            if topic:
                if topic.is_closed:
                    await update_user_disconnect_topic(session, user.id)
                    return await message.answer("Оператор закрыл диалог с вами")

            if message.text:
                await create_message(
                    session=session,
                    user_id=user.id,
                    id_message=message.message_id,
                    message=message.text,
                    topic_id=user.user_topic_id,
                )
            else:
                await create_message(
                    session=session,
                    user_id=user.id,
                    id_message=message.message_id,
                    message="Media content",
                    topic_id=user.user_topic_id,
                )
            try:
                return await message.bot.forward_message(
                    chat_id=settings.GROUP_ID_SUPPORT,
                    message_id=message.message_id,
                    message_thread_id=user.user_topic_id,
                    from_chat_id=message.chat.id,
                )
            except Exception as err:
                await update_user_disconnect_topic(session, user.id)
                return await message.answer("Оператор закрыл диалог с вами")

        operator_phrases = await get_phrases(session)

        if message.text and message.text.lower() in operator_phrases:
            try:
                topic = await message.bot.create_forum_topic(
                    chat_id=settings.GROUP_ID_SUPPORT,
                    name=f"Запрос от {message.from_user.full_name}",
                )
                user_message = await get_user_messages(session, user.id)
                for el in user_message[10:]:
                    text = (
                        f"Пользователь:\n\n{el.message}\n\n\nОтвет ИИ: {el.ai_message}"
                    )

                    if len(text) > 4000:
                        parts = [text[i : i + 4000] for i in range(0, len(text), 4000)]
                        for part in parts:
                            await message.bot.send_message(
                                chat_id=settings.GROUP_ID_SUPPORT,
                                text=part,
                                message_thread_id=topic.message_thread_id,
                            )
                            await asyncio.sleep(0.5)
                    else:
                        await message.bot.send_message(
                            chat_id=settings.GROUP_ID_SUPPORT,
                            text=text,
                            message_thread_id=topic.message_thread_id,
                        )

                    await asyncio.sleep(2)

                await message.bot.send_message(
                    chat_id=settings.GROUP_ID_SUPPORT,
                    text=f"Сообщение при котором вызвал пользователь тех поддержку:\n\n{message.text}",
                    message_thread_id=topic.message_thread_id,
                )

                await update_user_connect_topic(
                    session, message.from_user.id, topic.message_thread_id
                )
                await create_topic(
                    session,
                    f"Запрос от {message.from_user.full_name}",
                    topic.message_thread_id,
                    user.id,
                )
                await create_message(
                    session=session,
                    user_id=user.id,
                    id_message=message.message_id,
                    message=message.text,
                    topic_id=topic.message_thread_id,
                )

                return await message.answer(
                    "Ваш запрос передан оператору. Ожидайте ответа!"
                )

            except Exception as e:
                print(f"Ошибка при отправке сообщения оператору: {e}")
                return await message.answer(
                    "Произошла ошибка при соединении с оператором. Попробуйте позже."
                )

        if message.text:
            ai = await get_ai_use(session)

            history_messages = await get_user_history_messages(
                session, user.id, limit=30
            )

            messages_for_ai = [{"role": "system", "content": ai.system_prompt}]

            messages_for_ai.extend(history_messages)

            messages_for_ai.append({"role": "user", "content": message.text})

            ai = AI(messages_for_ai)
            result = await ai.send()

            if not result:
                return await message.answer(
                    "Ошибка не удалось авторизоваться в ИИ(возможно закончились деньги на балансе или удален токен)"
                )

            await create_message(
                session=session,
                user_id=user.id,
                id_message=message.message_id,
                message=message.text,
                ai_message=result,
            )
            return await message.answer(result, parse_mode="Markdown")
        else:
            return await message.answer(
                "К сожалению, я не могу анализировать фотографии. Пожалуйста, свяжитесь с оператором, и он вам поможет. Чтобы позвать оператора, просто напишите «Позови оператора»"
            )
