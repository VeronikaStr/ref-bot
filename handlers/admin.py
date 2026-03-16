from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from config import ADMIN_ID
from keyboards.admin_menu import admin_menu

router=Router()

@router.message(Command("admin"))
async def admin(message:Message):

    if message.from_user.id!=ADMIN_ID:
        return

    await message.answer(
        "👑 Админ панель",
        reply_markup=admin_menu()
    )