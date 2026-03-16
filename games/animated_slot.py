import random
import asyncio

symbols=["🍒","🍋","💎","7️⃣"]

async def spin(message):

    frames=["🎰 | | |","🎰 / / /","🎰 - - -"]

    for frame in frames:
        await message.edit_text(frame)
        await asyncio.sleep(0.5)

    result=[random.choice(symbols) for _ in range(3)]

    text=" ".join(result)

    win=result[0]==result[1]==result[2]

    return text,win