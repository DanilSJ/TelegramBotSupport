from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from app.echo.crud import create_user
from core.models import db_helper

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    async with db_helper.scoped_session_dependency() as session:
        user = await create_user(
            session, message.from_user.id, message.from_user.username
        )

        if user.is_block:
            return False
        await message.answer("Hello, world!")
