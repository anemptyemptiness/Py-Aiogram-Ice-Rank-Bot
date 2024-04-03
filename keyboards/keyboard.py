from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def create_places_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Мега Белая Дача", callback_data="place_mega_belaya_dacha")],
            [InlineKeyboardButton(text="Мега Нижний Новгород", callback_data="place_mega_nizh_novgorod")],
            [InlineKeyboardButton(text="Новая Рига Аутлет", callback_data="place_novaya_riga_autlet")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
        ],
    )


def create_yes_no_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="yes"),
             InlineKeyboardButton(text="Нет", callback_data="no")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
        ],
    )


def create_rules_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Согласен", callback_data="agree")],
        ],
    )


def create_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True,
    )
