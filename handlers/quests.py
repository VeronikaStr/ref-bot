from aiogram import Router
from aiogram.types import CallbackQuery

router=Router()

@router.callback_query(lambda c:c.data=="quests")
async def quests(callback:CallbackQuery):

    text="""
🎯 Задания

Пригласи 3 друзей — 50 монет
Сыграй 10 раз — 30 монет
"""

    await callback.message.answer(text)