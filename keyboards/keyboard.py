from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from callbacks.place import PlaceCallbackFactory
from db import DB


def create_places_kb() -> InlineKeyboardMarkup:
    kb = []

    for title, chat_id in DB.get_places_chat_id_title():
        kb.append([
            InlineKeyboardButton(text=title, callback_data=PlaceCallbackFactory(
                title=title,
                chat_id=int(chat_id),
                ).pack(),
            )
        ])

    kb.append([InlineKeyboardButton(text="Отмена", callback_data="cancel")])

    return InlineKeyboardMarkup(
        inline_keyboard=kb,
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
            [InlineKeyboardButton(text="Ознакомился", callback_data="agree")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
        ],
    )


def create_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True,
    )
