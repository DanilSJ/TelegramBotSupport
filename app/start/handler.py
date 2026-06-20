from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from app.echo.crud import create_user
from app.start.crud import get_start_text
from core.models import db_helper

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    async with db_helper.scoped_session_dependency() as session:
        user = await create_user(
            session, message.from_user.id, message.from_user.username
        )

        if user.is_block:
            return False

        text = await get_start_text(session)
        if not text or not text.is_use:
            return await message.answer("Админ не задал текст для /start")
        return await message.answer(text.text, parse_mode="Markdown")
