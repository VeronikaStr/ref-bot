from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from database import create_user
from keyboards.menu import menu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    await create_user(user_id)   # создаст пользователя, если его нет
    await message.answer(
        "🎰 Добро пожаловать в Casino Pro!",
        reply_markup=menu()
    )
