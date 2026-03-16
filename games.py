import random
from aiogram import types
from database import update_balance, add_xp

# Ставки и экономические игры
async def play_dice_game(user_id, message: types.Message, game_type: str):
    dice = None
    if game_type == "basketball":
        dice = await message.answer_dice(emoji="🏀")
    elif game_type == "darts":
        dice = await message.answer_dice(emoji="🎯")
    elif game_type == "bowling":
        dice = await message.answer_dice(emoji="🎳")
    elif game_type == "slot":
        dice = await message.answer_dice(emoji="🎰")

    # Эмулируем выигрыш/проигрыш
    value = dice.dice.value
    if value > 3:
        reward = value * 10
        update_balance(user_id, reward)
        add_xp(user_id, value*5)
        return f"🎉 Вы выиграли {reward} монет!"
    else:
        loss = value * 5
        update_balance(user_id, -loss)
        add_xp(user_id, value*2)
        return f"💔 Вы проиграли {loss} монет."

# Колесо удачи
def spin_wheel(user_id):
    outcomes = [50, 100, 0, 200, 0, 500]
    result = random.choice(outcomes)
    update_balance(user_id, result)
    return f"🎡 Вы выиграли {result} монет!"

# Сундуки
def open_case(user_id):
    rewards = [10, 50, 100, 200, 500]
    reward = random.choice(rewards)
    update_balance(user_id, reward)
    return f"📦 Вы получили {reward} монет из сундука!"

# Риск-игра
def risk_game(user_id, amount):
    if random.choice([True, False]):
        update_balance(user_id, amount)
        return f"💰 Вы удвоили ставку и получили {amount} монет!"
    else:
        update_balance(user_id, -amount)
        return f"💸 Вы проиграли {amount} монет."