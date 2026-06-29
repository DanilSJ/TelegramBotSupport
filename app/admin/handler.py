import os

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
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
    create_or_update_start,
    get_phrases,
    create_phrase,
    delete_phrase,
    get_system_prompt,
    update_system_prompt,
)
from app.echo.crud import create_user
from app.start.crud import get_start_text

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
    waiting_for_start_text = State()
    waiting_for_start_status = State()
    waiting_for_operator_telegram_id = State()
    waiting_for_phrase_text = State()
    waiting_for_phrase_delete_id = State()
    waiting_for_system_prompt_edit = State()


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
                text="👨‍💼 Управление операторами",
                callback_data="admin_manage_operators",
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
        [
            InlineKeyboardButton(
                text="⚙️ Изменить системный промпт",
                callback_data="admin_edit_system_prompt",
            )
        ],
        [
            InlineKeyboardButton(
                text="📝 Управление /start текстом", callback_data="admin_manage_start"
            )
        ],
        [
            InlineKeyboardButton(
                text="📚 Управление фразами", callback_data="admin_manage_phrases"
            )
        ],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_close")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    await state.clear()
    async with db_helper.scoped_session_dependency() as session:
        user = await create_user(
            session, message.from_user.id, message.from_user.username
        )
        if user.is_admin:
            return await message.answer(
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


@router.callback_query(F.data == "admin_manage_start")
async def admin_manage_start(callback: CallbackQuery, state: FSMContext):
    async with db_helper.scoped_session_dependency() as session:
        start_text = await get_start_text(session)

        if not start_text:
            start_text = await create_or_update_start(
                session,
                text="👋 Привет! Я бот для общения с AI.\n\n"
                "Используй /start для начала работы.\n"
                "Отправь любое сообщение, чтобы начать диалог.",
                is_use=True,
            )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✏️ Редактировать текст",
                        callback_data="admin_edit_start_text",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔄 Включить/Отключить",
                        callback_data="admin_toggle_start_status",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👁️ Просмотреть текущий текст",
                        callback_data="admin_view_start_text",
                    )
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
            ]
        )

        status = "✅ Активен" if start_text.is_use else "❌ Неактивен"

        await callback.message.edit_text(
            f"📝 Управление /start текстом\n\n"
            f"📌 Текущий статус: {status}\n"
            f"📌 Текст (превью): {start_text.text[:100]}...\n\n"
            f"Выберите действие:",
            reply_markup=keyboard,
        )
        await callback.answer()


@router.callback_query(F.data == "admin_edit_start_text")
async def admin_edit_start_text(callback: CallbackQuery, state: FSMContext):
    async with db_helper.scoped_session_dependency() as session:
        start_text = await get_start_text(session)

        await callback.message.edit_text(
            f"✏️ Редактирование /start текста\n\n"
            f"📌 Текущий текст:\n{start_text.text}\n\n"
            f"📝 Введите новый текст в формате Markdown:\n"
            f"Поддерживаются: **жирный**, *курсив*, `код`, [ссылки](url), списки и т.д.\n\n"
            f"Пример:\n"
            f"**Привет!** 👋\n"
            f"Я бот для *общения* с AI.\n\n"
            f"📌 Чтобы отменить, напишите /cancel"
        )
        await state.set_state(AdminStates.waiting_for_start_text)
        await callback.answer()


@router.message(AdminStates.waiting_for_start_text)
async def admin_save_start_text(message: Message, state: FSMContext):
    text = message.text.strip()

    if not text:
        await message.answer("❌ Текст не может быть пустым. Попробуйте снова:")
        return

    async with db_helper.scoped_session_dependency() as session:
        # Получаем текущий объект Start, чтобы сохранить статус
        from sqlalchemy import select
        from core.models import Start

        stmt = select(Start)
        result = await session.execute(stmt)
        current_start = result.scalar_one_or_none()
        is_use = current_start.is_use if current_start else False

        start = await create_or_update_start(session, text=text, is_use=is_use)

        await message.answer(
            f"✅ /start текст успешно обновлен!\n\n"
            f"📌 Новый текст:\n{start.text}\n"
            f"📌 Статус: {'✅ Активен' if start.is_use else '❌ Неактивен'}\n\n"
            f"Теперь при команде /start будет отображаться этот текст."
        )

    await state.clear()
    await message.answer(
        "Выберите следующее действие:", reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "admin_toggle_start_status")
async def admin_toggle_start_status(callback: CallbackQuery):
    async with db_helper.scoped_session_dependency() as session:
        from sqlalchemy import select
        from core.models import Start

        stmt = select(Start)
        result = await session.execute(stmt)
        current_start = result.scalar_one_or_none()

        if not current_start:
            # Если записи нет, создаем с дефолтным текстом
            start = await create_or_update_start(
                session, text="👋 Привет! Я бот для общения с AI.", is_use=True
            )
        else:
            # Переключаем статус
            current_start.is_use = not current_start.is_use
            await session.commit()
            await session.refresh(current_start)
            start = current_start

        status = "включен" if start.is_use else "выключен"
        await callback.message.edit_text(
            f"✅ /start текст успешно {status}!\n\n"
            f"📌 Текущий статус: {'✅ Активен' if start.is_use else '❌ Неактивен'}\n"
            f"📌 Текст: {start.text[:100]}...\n\n"
            f"Теперь при команде /start будет {'отображаться' if start.is_use else 'НЕ отображаться'} этот текст."
        )

        # Возвращаем в меню управления через пару секунд
        await callback.answer(f"/start {status}!")

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✏️ Редактировать текст",
                        callback_data="admin_edit_start_text",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔄 Включить/Отключить",
                        callback_data="admin_toggle_start_status",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👁️ Просмотреть текущий текст",
                        callback_data="admin_view_start_text",
                    )
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
            ]
        )

        await callback.message.edit_text(
            f"📝 Управление /start текстом\n\n"
            f"📌 Текущий статус: {'✅ Активен' if start.is_use else '❌ Неактивен'}\n"
            f"📌 Текст (превью): {start.text[:100]}...\n\n"
            f"Выберите действие:",
            reply_markup=keyboard,
        )


@router.callback_query(F.data == "admin_view_start_text")
async def admin_view_start_text(callback: CallbackQuery):
    async with db_helper.scoped_session_dependency() as session:
        start_text = await get_start_text(session)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", callback_data="admin_manage_start"
                    )
                ]
            ]
        )

        await callback.message.edit_text(
            f"👁️ Текущий /start текст:\n\n"
            f"{start_text.text}\n\n"
            f"📌 Статус: {'✅ Активен' if start_text.is_use else '❌ Неактивен'}\n"
            f"📌 ID: {start_text.id}\n"
            f"📌 Создан: {start_text.create_at.strftime('%d.%m.%Y %H:%M') if start_text.create_at else 'Неизвестно'}\n",
            reply_markup=keyboard,
        )
        await callback.answer()


@router.callback_query(F.data == "admin_manage_operators")
async def admin_manage_operators(callback: CallbackQuery, state: FSMContext):
    """Меню управления операторами"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить оператора",
                    callback_data="admin_add_operator",
                )
            ],
            [
                InlineKeyboardButton(
                    text="➖ Удалить оператора",
                    callback_data="admin_remove_operator",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Список операторов",
                    callback_data="admin_list_operators",
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
        ]
    )

    await callback.message.edit_text(
        "👨‍💼 Управление операторами\n\n"
        "Операторы имеют доступ к админ-панели, но не могут управлять AI моделями.\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_operator")
async def admin_add_operator_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса добавления оператора"""
    await callback.message.edit_text(
        "➕ Добавление оператора\n\n"
        "Введите Telegram ID пользователя, которого хотите сделать оператором:"
    )
    await state.set_state(AdminStates.waiting_for_operator_telegram_id)
    await state.update_data(action="add")
    await callback.answer()


@router.message(AdminStates.waiting_for_operator_telegram_id)
async def admin_operator_process(message: Message, state: FSMContext):
    """Обработка ввода Telegram ID для оператора"""
    try:
        telegram_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный числовой ID:")
        return

    data = await state.get_data()
    action = data.get("action")

    async with db_helper.scoped_session_dependency() as session:
        from .crud import make_user_operator

        user = await make_user_operator(session, telegram_id)

        if not user:
            await message.answer(
                "❌ Пользователь с таким Telegram ID не найден.\n"
                "Попробуйте снова или напишите /admin для выхода."
            )
            await state.clear()
            return

        action_text = "добавлен" if user.is_operator else "удален"

        await message.answer(
            f"✅ Пользователь {user.username or telegram_id} успешно {action_text}!\n"
            f"👤 ID: {user.telegram_id}\n"
            f"👨‍💼 Статус оператора: {'✅ Да' if user.is_operator else '❌ Нет'}\n"
            f"👑 Админ: {'✅ Да' if user.is_admin else '❌ Нет'}"
        )

    await state.clear()
    await message.answer(
        "Выберите следующее действие:", reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "admin_remove_operator")
async def admin_remove_operator_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса удаления оператора"""
    await callback.message.edit_text(
        "➖ Удаление оператора\n\n"
        "Введите Telegram ID пользователя, которого хотите удалить из операторов:"
    )
    await state.set_state(AdminStates.waiting_for_operator_telegram_id)
    await state.update_data(action="remove")
    await callback.answer()


@router.callback_query(F.data == "admin_list_operators")
async def admin_list_operators(callback: CallbackQuery):
    """Показывает список всех операторов"""
    async with db_helper.scoped_session_dependency() as session:
        from sqlalchemy import select
        from core.models import User

        stmt = select(User).where(User.is_operator == True)
        result = await session.execute(stmt)
        operators = result.scalars().all()

        if not operators:
            await callback.message.edit_text(
                "📋 Список операторов\n\n"
                "❌ Операторы не найдены.\n\n"
                "Чтобы добавить оператора, используйте кнопку 'Добавить оператора'.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Назад", callback_data="admin_manage_operators"
                            )
                        ]
                    ]
                ),
            )
            await callback.answer()
            return

        text = "📋 Список операторов:\n\n"
        for i, operator in enumerate(operators, 1):
            text += f"{i}. 👤 {operator.username or 'Без имени'}\n"
            text += f"   🆔 ID: {operator.telegram_id}\n"
            text += f"   👑 Админ: {'✅' if operator.is_admin else '❌'}\n\n"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", callback_data="admin_manage_operators"
                    )
                ]
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()


@router.callback_query(F.data == "admin_manage_phrases")
async def admin_manage_phrases(callback: CallbackQuery):
    """Меню управления фразами"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить фразу",
                    callback_data="admin_add_phrase",
                )
            ],
            [
                InlineKeyboardButton(
                    text="➖ Удалить фразу",
                    callback_data="admin_remove_phrase",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Список всех фраз",
                    callback_data="admin_list_phrases",
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
        ]
    )

    async with db_helper.scoped_session_dependency() as session:
        phrases = await get_phrases(session)
        count = len(phrases) if phrases else 0

        await callback.message.edit_text(
            f"📚 Управление фразами\n\n"
            f"📌 Всего фраз в базе: {count}\n\n"
            f"Фразы используются для автоматических ответов бота.\n"
            f"Выберите действие:",
            reply_markup=keyboard,
        )
        await callback.answer()


@router.callback_query(F.data == "admin_add_phrase")
async def admin_add_phrase_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления фразы"""
    await callback.message.edit_text(
        "➕ Добавление новой фразы\n\n"
        "Введите текст фразы, которую хотите добавить в базу данных:\n\n"
        "📝 Пример: 'Привет! Как дела?'"
    )
    await state.set_state(AdminStates.waiting_for_phrase_text)
    await callback.answer()


@router.message(AdminStates.waiting_for_phrase_text)
async def admin_add_phrase_process(message: Message, state: FSMContext):
    """Обработка добавления фразы"""
    phrase_text = message.text.strip()

    if not phrase_text:
        await message.answer("❌ Текст фразы не может быть пустым. Попробуйте снова:")
        return

    async with db_helper.scoped_session_dependency() as session:
        phrase = await create_phrase(session, phrase_text)

        await message.answer(
            f"✅ Фраза успешно добавлена!\n\n"
            f"📌 ID: {phrase.id}\n"
            f"📌 Текст: {phrase.phrase}\n"
            f"📌 Создана: {phrase.create_at.strftime('%d.%m.%Y %H:%M') if phrase.create_at else 'Неизвестно'}"
        )

    await state.clear()
    await message.answer(
        "Выберите следующее действие:", reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "admin_remove_phrase")
async def admin_remove_phrase_start(callback: CallbackQuery, state: FSMContext):
    """Начало удаления фразы"""
    async with db_helper.scoped_session_dependency() as session:
        phrases = await get_phrases(session)

        if not phrases:
            await callback.message.edit_text(
                "❌ В базе данных нет фраз для удаления.\n\n"
                "Сначала добавьте фразы через '➕ Добавить фразу'.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Назад", callback_data="admin_manage_phrases"
                            )
                        ]
                    ]
                ),
            )
            await callback.answer()
            return

        # Создаем клавиатуру с выбором фразы для удаления
        keyboard_buttons = []
        for phrase in phrases[:10]:  # Показываем первые 10 фраз
            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"❌ #{phrase.id}: {phrase.phrase[:30]}...",
                        callback_data=f"admin_delete_phrase_{phrase.id}",
                    )
                ]
            )

        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text="🔙 Назад", callback_data="admin_manage_phrases"
                )
            ]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        text = "➖ Удаление фразы\n\n"
        text += "Выберите фразу для удаления:\n\n"
        for phrase in phrases[:10]:
            text += f"• #{phrase.id}: {phrase.phrase[:50]}...\n"

        if len(phrases) > 10:
            text += f"\n... и еще {len(phrases) - 10} фраз"

        await callback.message.edit_text(text, reply_markup=keyboard)
        await state.set_state(AdminStates.waiting_for_phrase_delete_id)
        await callback.answer()


@router.callback_query(F.data.startswith("admin_delete_phrase_"))
async def admin_delete_phrase_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления фразы"""
    phrase_id = int(callback.data.split("_")[3])
    await state.update_data(delete_phrase_id=phrase_id)

    async with db_helper.scoped_session_dependency() as session:
        from sqlalchemy import select
        from core.models import Phrase

        stmt = select(Phrase).where(Phrase.id == phrase_id)
        result = await session.execute(stmt)
        phrase = result.scalar_one_or_none()

        if not phrase:
            await callback.message.edit_text(
                "❌ Фраза не найдена. Возможно, она уже была удалена.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Назад", callback_data="admin_manage_phrases"
                            )
                        ]
                    ]
                ),
            )
            await callback.answer()
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Да, удалить",
                        callback_data="admin_confirm_delete_phrase",
                    ),
                    InlineKeyboardButton(
                        text="❌ Отмена", callback_data="admin_cancel_delete_phrase"
                    ),
                ]
            ]
        )

        await callback.message.edit_text(
            f"⚠️ Вы уверены, что хотите удалить эту фразу?\n\n"
            f"📌 ID: {phrase.id}\n"
            f"📌 Текст: {phrase.phrase}\n\n"
            f"Это действие нельзя отменить!",
            reply_markup=keyboard,
        )
        await callback.answer()


@router.callback_query(F.data == "admin_confirm_delete_phrase")
async def admin_delete_phrase_process(callback: CallbackQuery, state: FSMContext):
    """Обработка удаления фразы"""
    data = await state.get_data()
    phrase_id = data.get("delete_phrase_id")

    if not phrase_id:
        await callback.message.edit_text("❌ Ошибка: ID фразы не найден")
        await state.clear()
        return

    async with db_helper.scoped_session_dependency() as session:
        success = await delete_phrase(session, phrase_id)

        if success:
            await callback.message.edit_text(
                f"✅ Фраза с ID {phrase_id} успешно удалена из базы данных!"
            )
        else:
            await callback.message.edit_text(
                f"❌ Не удалось удалить фразу с ID {phrase_id}. Возможно, она не существует."
            )

    await state.clear()
    await callback.message.answer(
        "Выберите следующее действие:", reply_markup=get_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_cancel_delete_phrase")
async def admin_delete_phrase_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена удаления фразы"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Удаление фразы отменено",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", callback_data="admin_manage_phrases"
                    )
                ]
            ]
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_list_phrases")
async def admin_list_phrases(callback: CallbackQuery):
    """Показывает список всех фраз"""
    async with db_helper.scoped_session_dependency() as session:
        phrases = await get_phrases(session)

        if not phrases:
            await callback.message.edit_text(
                "📋 Список фраз\n\n"
                "❌ Фразы не найдены.\n\n"
                "Чтобы добавить фразу, используйте кнопку 'Добавить фразу'.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Назад", callback_data="admin_manage_phrases"
                            )
                        ]
                    ]
                ),
            )
            await callback.answer()
            return

        # Разбиваем список на страницы (по 10 фраз)
        pages = [phrases[i : i + 10] for i in range(0, len(phrases), 10)]
        current_page = 0

        text = f"📋 Список фраз (страница {current_page + 1}/{len(pages)}):\n\n"
        for i, phrase in enumerate(pages[current_page], 1):
            text += f"{i}. #{phrase.id}: {phrase.phrase}\n"

        # Добавляем навигацию по страницам
        keyboard_buttons = []
        if len(pages) > 1:
            nav_buttons = []
            if current_page > 0:
                nav_buttons.append(
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data=f"admin_phrases_page_{current_page - 1}",
                    )
                )
            if current_page < len(pages) - 1:
                nav_buttons.append(
                    InlineKeyboardButton(
                        text="Вперед ➡️",
                        callback_data=f"admin_phrases_page_{current_page + 1}",
                    )
                )
            if nav_buttons:
                keyboard_buttons.append(nav_buttons)

        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text="🔙 Назад", callback_data="admin_manage_phrases"
                )
            ]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()


@router.callback_query(F.data.startswith("admin_phrases_page_"))
async def admin_phrases_page(callback: CallbackQuery):
    """Переключение страниц списка фраз"""
    page = int(callback.data.split("_")[3])

    async with db_helper.scoped_session_dependency() as session:
        phrases = await get_phrases(session)

        if not phrases:
            await callback.answer("Фразы не найдены")
            return

        pages = [phrases[i : i + 10] for i in range(0, len(phrases), 10)]
        current_page = page

        if current_page >= len(pages) or current_page < 0:
            await callback.answer("Страница не найдена")
            return

        text = f"📋 Список фраз (страница {current_page + 1}/{len(pages)}):\n\n"
        for i, phrase in enumerate(pages[current_page], 1):
            text += f"{i}. #{phrase.id}: {phrase.phrase}\n"

        keyboard_buttons = []
        if len(pages) > 1:
            nav_buttons = []
            if current_page > 0:
                nav_buttons.append(
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data=f"admin_phrases_page_{current_page - 1}",
                    )
                )
            if current_page < len(pages) - 1:
                nav_buttons.append(
                    InlineKeyboardButton(
                        text="Вперед ➡️",
                        callback_data=f"admin_phrases_page_{current_page + 1}",
                    )
                )
            if nav_buttons:
                keyboard_buttons.append(nav_buttons)

        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text="🔙 Назад", callback_data="admin_manage_phrases"
                )
            ]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()


@router.callback_query(F.data == "admin_edit_system_prompt")
async def admin_edit_system_prompt(callback: CallbackQuery, state: FSMContext):
    """Просмотр и изменение системного промпта активной AI модели"""
    async with db_helper.scoped_session_dependency() as session:
        ai = await get_system_prompt(session)

        if not ai:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
                ]
            )
            await callback.message.edit_text(
                "❌ Активная AI модель не найдена.\n\n"
                "Сначала создайте и активируйте AI модель через:\n"
                "• 'Создать новую AI модель'\n"
                "• 'Выбрать AI'",
                reply_markup=keyboard,
            )
            await callback.answer()
            return

        # Обрезаем промпт для превью, но безопасно
        prompt_preview = ai.system_prompt[:150] if ai.system_prompt else "(пусто)"
        if len(ai.system_prompt) > 150:
            prompt_preview += "..."

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✏️ Изменить системный промпт",
                        callback_data="admin_change_system_prompt",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👁️ Просмотреть полный промпт",
                        callback_data="admin_view_system_prompt",
                    )
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
            ]
        )

        await callback.message.edit_text(
            f"⚙️ Управление системным промптом\n\n"
            f"📌 Активная модель: {ai.model}\n"
            f"📌 Текущий промпт (превью):\n<code>{prompt_preview}</code>\n\n"
            f"Выберите действие:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
        await callback.answer()


@router.callback_query(F.data == "admin_view_system_prompt")
async def admin_view_system_prompt(callback: CallbackQuery):
    """Просмотр полного системного промпта"""
    async with db_helper.scoped_session_dependency() as session:
        ai = await get_system_prompt(session)

        if not ai:
            await callback.message.edit_text(
                "❌ Активная AI модель не найдена.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Назад",
                                callback_data="admin_edit_system_prompt",
                            )
                        ]
                    ]
                ),
            )
            await callback.answer()
            return

        # Обрезаем системный промпт, если он слишком длинный
        max_length = 3500  # Оставляем запас для остального текста
        prompt_text = ai.system_prompt

        if len(prompt_text) > max_length:
            # Обрезаем и добавляем индикатор, что текст обрезан
            prompt_text = (
                prompt_text[:max_length]
                + "\n\n... (текст обрезан из-за ограничений Telegram)"
            )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✏️ Изменить", callback_data="admin_change_system_prompt"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", callback_data="admin_edit_system_prompt"
                    )
                ],
            ]
        )

        await callback.message.edit_text(
            f"👁️ Полный системный промпт:\n\n"
            f"📌 Модель: {ai.model}\n"
            f"📌 ID: {ai.id}\n\n"
            f"📝 Текст промпта:\n"
            f"<pre>{prompt_text}</pre>\n\n"
            f"Вы можете отредактировать его, нажав 'Изменить'.",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        await callback.answer()


@router.callback_query(F.data == "admin_change_system_prompt")
async def admin_change_system_prompt_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса изменения системного промпта"""
    async with db_helper.scoped_session_dependency() as session:
        ai = await get_system_prompt(session)

        if not ai:
            await callback.message.edit_text(
                "❌ Активная AI модель не найдена.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Назад",
                                callback_data="admin_edit_system_prompt",
                            )
                        ]
                    ]
                ),
            )
            await callback.answer()
            return

        await state.update_data(current_system_prompt=ai.system_prompt)

        # Обрезаем системный промпт, если он слишком длинный
        max_length = 3500
        prompt_text = ai.system_prompt

        if len(prompt_text) > max_length:
            prompt_text = (
                prompt_text[:max_length]
                + "\n\n... (текст обрезан из-за ограничений Telegram)"
            )

        await callback.message.edit_text(
            f"✏️ Изменение системного промпта\n\n"
            f"📌 Текущая модель: {ai.model}\n"
            f"📌 Текущий промпт:\n{prompt_text}\n\n"
            f"📝 Введите новый системный промпт текстом\n"
            f"📎 ИЛИ отправьте текстовый файл (.txt, .md, .json и т.д.)\n\n"
            f"💡 Системный промпт определяет поведение AI.\n"
            f"Например: 'Ты - полезный ассистент, который помогает пользователям.'\n\n"
            f"Чтобы отменить, напишите /cancel"
        )
        await state.set_state(AdminStates.waiting_for_system_prompt_edit)
        await callback.answer()


@router.message(AdminStates.waiting_for_system_prompt_edit)
async def admin_save_system_prompt(message: Message, state: FSMContext):
    """Сохранение нового системного промпта из текста или файла"""

    new_prompt = None
    is_from_file = False

    # Проверяем, является ли сообщение текстом
    if message.text and not message.text.startswith("/"):
        new_prompt = message.text.strip()
        if not new_prompt:
            await message.answer("❌ Промпт не может быть пустым. Попробуйте снова:")
            return

    # Проверяем, является ли сообщение файлом
    elif message.document:
        try:
            # Получаем информацию о файле
            document = message.document

            # Проверяем размер файла (максимум 5MB)
            if document.file_size > 5 * 1024 * 1024:
                await message.answer(
                    "❌ Файл слишком большой! Максимальный размер: 5MB.\n"
                    "Пожалуйста, отправьте файл меньшего размера или введите текст вручную."
                )
                return

            # Проверяем расширение файла
            allowed_extensions = {
                ".txt",
                ".md",
                ".json",
                ".xml",
                ".yaml",
                ".yml",
                ".csv",
                ".log",
            }
            file_extension = os.path.splitext(document.file_name)[1].lower()

            if file_extension not in allowed_extensions:
                await message.answer(
                    f"❌ Неподдерживаемый тип файла: {file_extension}\n"
                    f"Поддерживаются: {', '.join(allowed_extensions)}\n"
                    f"Или введите текст вручную."
                )
                return

            # Скачиваем файл
            file_path = f"temp_{document.file_name}"
            await message.bot.download(document.file_id, destination=file_path)

            # Читаем содержимое файла
            try:
                # Определяем кодировку файла
                import chardet

                with open(file_path, "rb") as f:
                    raw_data = f.read()
                    encoding = chardet.detect(raw_data)["encoding"] or "utf-8"

                with open(file_path, "r", encoding=encoding) as f:
                    new_prompt = f.read().strip()

                # Удаляем временный файл
                os.remove(file_path)

                if not new_prompt:
                    await message.answer(
                        "❌ Файл пуст. Пожалуйста, отправьте непустой файл или введите текст вручную."
                    )
                    return

                is_from_file = True

            except UnicodeDecodeError:
                os.remove(file_path) if os.path.exists(file_path) else None
                await message.answer(
                    "❌ Не удалось прочитать файл. Убедитесь, что файл содержит текстовые данные.\n"
                    "Попробуйте сохранить файл в кодировке UTF-8 или введите текст вручную."
                )
                return
            except Exception as e:
                os.remove(file_path) if os.path.exists(file_path) else None
                await message.answer(
                    f"❌ Ошибка при чтении файла: {str(e)}\n"
                    "Пожалуйста, попробуйте снова или введите текст вручную."
                )
                return

        except Exception as e:
            await message.answer(
                f"❌ Ошибка при обработке файла: {str(e)}\n"
                "Пожалуйста, попробуйте снова или введите текст вручную."
            )
            return

    else:
        await message.answer(
            "❌ Пожалуйста, отправьте текст или текстовый файл.\n"
            "Поддерживаются файлы: .txt, .md, .json, .xml, .yaml, .yml, .csv, .log"
        )
        return

    # Сохраняем новый промпт
    async with db_helper.scoped_session_dependency() as session:
        ai = await update_system_prompt(session, new_prompt)

        if not ai:
            await message.answer(
                "❌ Активная AI модель не найдена.\n"
                "Сначала создайте и активируйте AI модель."
            )
            await state.clear()
            return

        # Формируем ответное сообщение
        response_text = (
            f"✅ Системный промпт успешно обновлен!\n\n" f"📌 Модель: {ai.model}\n"
        )

        if is_from_file:
            response_text += f"📎 Источник: файл {message.document.file_name}\n"

        # Показываем первые 200 символов нового промпта
        preview = new_prompt[:200]
        if len(new_prompt) > 200:
            preview += "..."

        response_text += f"📌 Новый промпт (начало):\n{preview}\n\n"
        response_text += f"📊 Длина промпта: {len(new_prompt)} символов\n\n"
        response_text += (
            f"Теперь AI будет использовать этот промпт для всех новых ответов."
        )

        await message.answer(response_text)

    await state.clear()
    await message.answer(
        "Выберите следующее действие:", reply_markup=get_admin_keyboard()
    )


@router.message(
    StateFilter(AdminStates.waiting_for_system_prompt_edit), F.text == "/cancel"
)
async def cancel_system_prompt_edit(message: Message, state: FSMContext):
    """Отмена изменения системного промпта"""
    await state.clear()
    await message.answer(
        "❌ Изменение системного промпта отменено.", reply_markup=get_admin_keyboard()
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Действие отменено.", reply_markup=get_admin_keyboard())
