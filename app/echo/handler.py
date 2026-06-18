from aiogram import Router, F
from aiogram.types import Message
from services.ai import AI

router = Router()


@router.message(F.text)
async def echo(message: Message):
    ai = AI(message.text)
    result = await ai.send()
    return await message.answer(result)
