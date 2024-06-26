from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from src.callbacks.place import PlaceCallbackFactory
from src.db import cached_places


def create_places_kb() -> InlineKeyboardMarkup:
    kb = []

    for title, chat_id in cached_places.items():
        kb.append([
            InlineKeyboardButton(text=title, callback_data=PlaceCallbackFactory(
                title=title,
                chat_id=int(chat_id),
                ).pack(),
            )
        ])

    kb.append([InlineKeyboardButton(text="➢ Отмена", callback_data="cancel")])

    return InlineKeyboardMarkup(
        inline_keyboard=kb,
    )


def create_yes_no_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="yes"),
             InlineKeyboardButton(text="Нет", callback_data="no")],
            [InlineKeyboardButton(text="➢ Отмена", callback_data="cancel")],
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


def create_good_or_bad_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Хорошее", callback_data="good"),
             InlineKeyboardButton(text="Плохое", callback_data="bad")],
            [InlineKeyboardButton(text="➢ Отмена", callback_data="cancel")],
        ]
    )


def create_salaries_checking_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отправить", callback_data="send_salaries")],
            [InlineKeyboardButton(text="Изменить текст", callback_data="rewrite_salaries")],
            [InlineKeyboardButton(text="➢ Отмена", callback_data="cancel")],
        ]
    )
