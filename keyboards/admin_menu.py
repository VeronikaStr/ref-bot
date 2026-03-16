from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton

def admin_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

        [InlineKeyboardButton(text="📊 Статистика",callback_data="stats")],

        [InlineKeyboardButton(text="📨 Рассылка",callback_data="broadcast")]
        ]
    )