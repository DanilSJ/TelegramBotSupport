from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core.models import db_helper
from .crud import (
    create_ai,
    update_ai_use,
    block_user,
    get_user_messages,
    update_ai_message,
    delete_message,
)

router = Router()


class AdminStates(StatesGroup):
    waiting_for_telegram_id = State()
    waiting_for_model = State()
    waiting_for_base_url = State()
    waiting_for_api_key = State()
    waiting_for_system_prompt = State()
    waiting_for_ai_id = State()
    waiting_for_user_messages = State()
    waiting_for_message_action = State()
    waiting_for_edit_message = State()
    waiting_for_delete_message = State()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="👤 Заблокировать/Разблокировать пользователя",
                callback_data="admin_block_user",
            )
        ],
        [
            InlineKeyboardButton(
                text="💬 Управление сообщениями пользователя",
                callback_data="admin_user_messages",
            )
        ],
        [
            InlineKeyboardButton(
                text="🤖 Создать новую AI модель", callback_data="admin_create_ai"
            )
        ],
        [InlineKeyboardButton(text="🔄 Выбрать AI", callback_data="admin_update_ai")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_close")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    await message.answer(
        "👋 Добро пожаловать в админ-панель!\nВыберите действие:",
        reply_markup=get_admin_keyboard(),
    )


@router.callback_query(F.data == "admin_close")
async def admin_close(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("Панель закрыта")


@router.callback_query(F.data == "admin_block_user")
async def admin_block_user_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔒 Введите Telegram ID пользователя для блокировки/разблокировки:"
    )
    await state.set_state(AdminStates.waiting_for_telegram_id)
    await callback.answer()


@router.message(AdminStates.waiting_for_telegram_id)
async def admin_block_user_process(message: Message, state: FSMContext):
    try:
        telegram_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный числовой ID:")
        return

    async with db_helper.scoped_session_dependency() as session:
        user = await block_user(session, telegram_id)

        if not user:
            await message.answer(
                "❌ Пользователь с таким Telegram ID не найден.\n"
                "Попробуйте снова или напишите /admin для выхода."
            )
            await state.clear()
            return

        status = "заблокирован" if user.is_block else "разблокирован"
        await message.answer(
            f"✅ Пользователь {user.username or telegram_id} успешно {status}!\n"
            f"Текущий статус: {'🔒 Заблокирован' if user.is_block else '🔓 Активен'}"
        )

    await state.clear()
    await message.answer(
        "Выберите следующее действие:", reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "admin_user_messages")
async def admin_user_messages_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💬 Введите Telegram ID пользователя, чтобы просмотреть его сообщения:"
    )
    await state.set_state(AdminStates.waiting_for_user_messages)
    await callback.answer()


@router.message(AdminStates.waiting_for_user_messages)
async def admin_user_messages_process(message: Message, state: FSMContext):
    try:
        telegram_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный числовой ID:")
        return

    async with db_helper.scoped_session_dependency() as session:
        messages = await get_user_messages(session, telegram_id, limit=20)

        if not messages:
            await message.answer(
                "❌ У пользователя нет сообщений или пользователь не найден."
            )
            await state.clear()
            return

        await state.update_data(telegram_id=telegram_id, messages=messages)

        text = f"📨 Последние сообщения пользователя (ID: {telegram_id}):\n\n"
        for i, msg in enumerate(messages[:5], 1):
            text += f"{i}. Сообщение: {msg.message[:50]}...\n"
            text += f"   Ответ AI: {msg.ai_message[:50] if msg.ai_message else 'Нет ответа'}\n"
            text += f"   ID: {msg.id}\n\n"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"📝 Редактировать сообщение #{i+1}",
                        callback_data=f"edit_msg_{msg.id}",
                    )
                ]
                for i, msg in enumerate(messages[:5])
            ]
            + [[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]]
        )

        await message.answer(text, reply_markup=keyboard)
        await state.set_state(AdminStates.waiting_for_message_action)


@router.callback_query(F.data.startswith("edit_msg_"))
async def admin_edit_message_start(callback: CallbackQuery, state: FSMContext):
    message_id = int(callback.data.split("_")[2])
    await state.update_data(edit_message_id=message_id)

    async with db_helper.scoped_session_dependency() as session:
        from sqlalchemy import select
        from core.models import Message

        stmt = select(Message).where(Message.id == message_id)
        result = await session.execute(stmt)
        msg = result.scalar_one_or_none()

        if not msg:
            await callback.message.answer("❌ Сообщение не найдено")
            return

        await callback.message.edit_text(
            f"📝 Редактирование сообщения:\n\n"
            f"Текущий текст: {msg.message}\n"
            f"Текущий ответ AI: {msg.ai_message if msg.ai_message else 'Нет ответа'}\n\n"
            f"Введите новый текст для AI сообщения:"
        )
        await state.set_state(AdminStates.waiting_for_edit_message)
        await callback.answer()


@router.message(AdminStates.waiting_for_edit_message)
async def admin_edit_message_process(message: Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("edit_message_id")
    telegram_id = data.get("telegram_id")

    if not message_id:
        await message.answer("❌ Ошибка: ID сообщения не найден")
        await state.clear()
        return

    new_text = message.text.strip()

    async with db_helper.scoped_session_dependency() as session:
        updated_message = await update_ai_message(session, message_id, new_text)

        if not updated_message:
            await message.answer("❌ Сообщение не найдено")
            await state.clear()
            return

        # Обновляем сообщение в Telegram
        try:
            # Получаем оригинальное сообщение из базы
            from sqlalchemy import select
            from core.models import Message as DBMessage

            stmt = select(DBMessage).where(DBMessage.id == message_id)
            result = await session.execute(stmt)
            msg = result.scalar_one_or_none()

            if msg and msg.id_message and telegram_id:
                # Отправляем обновленное сообщение пользователю
                await message.bot.edit_message_text(
                    chat_id=telegram_id, message_id=msg.id_message, text=new_text
                )
                await message.answer(
                    f"✅ Сообщение успешно обновлено!\n"
                    f"Новый текст: {new_text[:100]}..."
                )
        except Exception as e:
            await message.answer(
                f"✅ Сообщение обновлено в БД, но не удалось обновить в чате: {str(e)}"
            )

    await state.clear()
    await message.answer(
        "Выберите следующее действие:", reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data.startswith("delete_msg_"))
async def admin_delete_message_start(callback: CallbackQuery, state: FSMContext):
    message_id = int(callback.data.split("_")[2])
    await state.update_data(delete_message_id=message_id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить", callback_data="confirm_delete"
                ),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete"),
            ]
        ]
    )

    await callback.message.edit_text(
        "⚠️ Вы уверены, что хотите удалить это сообщение?\n"
        "Это действие нельзя отменить!",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_delete")
async def admin_delete_message_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("delete_message_id")
    telegram_id = data.get("telegram_id")

    if not message_id:
        await callback.message.answer("❌ Ошибка: ID сообщения не найден")
        await state.clear()
        return

    async with db_helper.scoped_session_dependency() as session:
        # Получаем сообщение перед удалением
        from sqlalchemy import select
        from core.models import Message as DBMessage

        stmt = select(DBMessage).where(DBMessage.id == message_id)
        result = await session.execute(stmt)
        msg = result.scalar_one_or_none()

        success = await delete_message(session, message_id)

        if not success:
            await callback.message.answer("❌ Сообщение не найдено")
            await state.clear()
            return

        # Пытаемся удалить сообщение в Telegram
        try:
            if msg and msg.id_message and telegram_id:
                await callback.bot.delete_message(
                    chat_id=telegram_id, message_id=msg.id_message
                )
                await callback.message.edit_text(
                    "✅ Сообщение успешно удалено из чата и БД!"
                )
        except Exception as e:
            await callback.message.edit_text(
                f"✅ Сообщение удалено из БД, но не удалось удалить из чата: {str(e)}"
            )

    await state.clear()
    await callback.message.answer(
        "Выберите следующее действие:", reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "cancel_delete")
async def admin_delete_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Удаление отменено")
    await callback.message.answer(
        "Выберите следующее действие:", reply_markup=get_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    await callback.message.edit_text(
        "👋 Добро пожаловать в админ-панель!\nВыберите действие:",
        reply_markup=get_admin_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_create_ai")
async def admin_create_ai_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🤖 Создание новой AI модели.\n\n"
        "Введите название модели (например: gpt-4, claude-3):"
    )
    await state.set_state(AdminStates.waiting_for_model)
    await callback.answer()


@router.message(AdminStates.waiting_for_model)
async def admin_create_ai_model(message: Message, state: FSMContext):
    await state.update_data(model=message.text.strip())
    await message.answer("🌐 Введите Base URL (например: https://api.openai.com/v1):")
    await state.set_state(AdminStates.waiting_for_base_url)


@router.message(AdminStates.waiting_for_base_url)
async def admin_create_ai_base_url(message: Message, state: FSMContext):
    await state.update_data(base_url=message.text.strip())
    await message.answer("🔑 Введите API Key:")
    await state.set_state(AdminStates.waiting_for_api_key)


@router.message(AdminStates.waiting_for_api_key)
async def admin_create_ai_api_key(message: Message, state: FSMContext):
    await state.update_data(api_key=message.text.strip())
    await message.answer("📝 Введите System Prompt (системный промпт):")
    await state.set_state(AdminStates.waiting_for_system_prompt)


@router.message(AdminStates.waiting_for_system_prompt)
async def admin_create_ai_system_prompt(message: Message, state: FSMContext):
    data = await state.get_data()

    async with db_helper.scoped_session_dependency() as session:
        ai = await create_ai(
            session,
            model=data["model"],
            base_url=data["base_url"],
            api_key=data["api_key"],
            system_prompt=message.text.strip(),
        )

        await message.answer(
            f"✅ AI модель успешно создана!\n\n"
            f"📌 ID: {ai.id}\n"
            f"📌 Модель: {ai.model}\n"
            f"📌 Base URL: {ai.base_url}\n"
            f"📌 System Prompt: {ai.system_prompt[:50]}...\n"
            f"📌 Активна: {'✅ Да' if ai.use else '❌ Нет'}"
        )

    await state.clear()
    await message.answer(
        "Выберите следующее действие:", reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "admin_update_ai")
async def admin_update_ai_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔄 Введите ID AI модели, которую хотите активировать:"
    )
    await state.set_state(AdminStates.waiting_for_ai_id)
    await callback.answer()


@router.message(AdminStates.waiting_for_ai_id)
async def admin_update_ai_process(message: Message, state: FSMContext):
    try:
        ai_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный числовой ID:")
        return

    async with db_helper.scoped_session_dependency() as session:
        ai = await update_ai_use(session, ai_id)

        if not ai:
            await message.answer(
                "❌ AI модель с таким ID не найдена.\n"
                "Попробуйте снова или напишите /admin для выхода."
            )
            await state.clear()
            return

        await message.answer(
            f"✅ AI модель успешно активирована!\n\n"
            f"📌 ID: {ai.id}\n"
            f"📌 Модель: {ai.model}\n"
            f"📌 Base URL: {ai.base_url}\n"
            f"📌 Активна: {'✅ Да' if ai.use else '❌ Нет'}"
        )

    await state.clear()
    await message.answer(
        "Выберите следующее действие:", reply_markup=get_admin_keyboard()
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Действие отменено.", reply_markup=get_admin_keyboard())
