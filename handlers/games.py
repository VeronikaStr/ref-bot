from aiogram import Router
from aiogram.types import CallbackQuery
from games.animated_slot import spin
from games.wheel import spin as wheel_spin
from database import add_balance
from utils.anti_abuse import check

router=Router()

@router.callback_query(lambda c:c.data=="slot")
async def slot(callback:CallbackQuery):

    if not check(callback.from_user.id):
        return

    msg=await callback.message.answer("🎰 Крутим...")

    result,win=await spin(msg)

    if win:
        await add_balance(callback.from_user.id,50)
        text=f"{result}\n\n🎉 Выигрыш 50 монет!"
    else:
        text=f"{result}\n\nПопробуй снова"

    await msg.edit_text(text)


@router.callback_query(lambda c:c.data=="wheel")
async def wheel(callback:CallbackQuery):

    reward=wheel_spin()

    if reward=="jackpot":
        reward=500

    await add_balance(callback.from_user.id,reward)

    await callback.message.answer(
        f"🎡 Колесо остановилось\n\n🎁 {reward} монет"
    )