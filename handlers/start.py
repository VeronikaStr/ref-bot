from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from keyboards.menu import menu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🎰 Добро пожаловать в Casino Pro!\n\n"
        "Выберите игру:",
        reply_markup=menu()
    )
