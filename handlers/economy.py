from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import get_user

router = Router()

@router.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await get_user(user_id)
    if user:
        balance = user['balance']
        exp = user['exp']
        level = user['level']
        text = (f"📊 <b>Ваш профиль</b>\n\n"
                f"💰 Баланс: {balance} монет\n"
                f"⭐ Опыт: {exp}\n"
                f"📈 Уровень: {level}")
    else:
        text = "❌ Данные не найдены. Начните с /start"
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "bonus")
async def bonus_callback(callback: CallbackQuery):
    await callback.message.answer("🎁 Ежедневный бонус пока в разработке!")
    await callback.answer()