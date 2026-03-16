from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton

def menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

        [InlineKeyboardButton(text="🎰 Слот",callback_data="slot")],

        [InlineKeyboardButton(text="🎡 Колесо",callback_data="wheel")],

        [InlineKeyboardButton(text="🎁 Бонус",callback_data="bonus")],

        [InlineKeyboardButton(text="📊 Профиль",callback_data="profile")],

        [InlineKeyboardButton(text="🎯 Задания",callback_data="quests")]
        ]
    )