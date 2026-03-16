from aiogram import Router
from aiogram.types import Message
from database import create_user
from keyboards.menu import menu

router = Router()

@router.message(commands=["start"])
async def cmd_start(message: Message):
    # Создаём пользователя в базе
    await create_user(message.from_user.id)

    # Приветственное сообщение
    text = f"Привет, {message.from_user.full_name}! 👋\n\n" \
           f"Добро пожаловать в казино бота! 🎰\n" \
           f"Вы можете играть в слоты, крутить колесо удачи и выполнять задания."

    await message.answer(text, reply_markup=menu())