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
from .crud import create_ai, update_ai_use, block_user

router = Router()


class AdminStates(StatesGroup):
    waiting_for_telegram_id = State()
    waiting_for_model = State()
    waiting_for_base_url = State()
    waiting_for_api_key = State()
    waiting_for_system_prompt = State()
    waiting_for_ai_id = State()


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
