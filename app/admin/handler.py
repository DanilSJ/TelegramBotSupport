from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from core.models import db_helper

router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    async with db_helper.scoped_session_dependency() as session:
        pass
