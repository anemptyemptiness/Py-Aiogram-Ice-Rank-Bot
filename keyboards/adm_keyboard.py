from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from callbacks.employee import EmployeeCallbackFactory
from callbacks.admin import AdminCallbackFactory
from callbacks.place import PlaceCallbackFactory
from db import DB


def create_admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить сотрудника", callback_data="add_employee")],
            [InlineKeyboardButton(text="Удалить сотрудника", callback_data="delete_employee")],
            [InlineKeyboardButton(text="Список сотрудников", callback_data="employee_list")],
            [InlineKeyboardButton(text="Добавить админа", callback_data="add_admin")],
            [InlineKeyboardButton(text="Удалить админа", callback_data="delete_admin")],
            [InlineKeyboardButton(text="Список админов", callback_data="admin_list")],
            [InlineKeyboardButton(text="Добавить точку", callback_data="add_place")],
            [InlineKeyboardButton(text="Удалить точку", callback_data="delete_place")],
            [InlineKeyboardButton(text="Список точек", callback_data="places_list")],
            [InlineKeyboardButton(text="Выход с админки", callback_data="adm_exit")],
        ]
    )


def check_add_employee() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить сотрудника", callback_data="access_employee")],
            [InlineKeyboardButton(text="Изменить имя", callback_data="rename_employee")],
            [InlineKeyboardButton(text="Изменить id", callback_data="reid_employee")],
            [InlineKeyboardButton(text="Изменить username", callback_data="reusername_employee")],
        ]
    )


def check_add_admin() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить администратора", callback_data="access_admin")],
            [InlineKeyboardButton(text="Изменить имя", callback_data="rename_admin")],
            [InlineKeyboardButton(text="Изменить id", callback_data="reid_admin")],
            [InlineKeyboardButton(text="Изменить username", callback_data="reusername_admin")],
        ]
    )


def check_add_place() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить точку", callback_data="access_place")],
            [InlineKeyboardButton(text="Изменить название", callback_data="rename_place")],
            [InlineKeyboardButton(text="Изменить id чата точки", callback_data="reid_place")],
        ]
    )


def create_employee_list_kb() -> InlineKeyboardMarkup:
    kb = []

    for fullname, user_id in DB.get_employees_fullnames_ids():
        kb.append([
            InlineKeyboardButton(
                text=f"{fullname}",
                callback_data=EmployeeCallbackFactory(
                    user_id=user_id,
                ).pack(),
            )
        ])

    kb.append([InlineKeyboardButton(text="➢ Назад", callback_data="go_back")])

    return InlineKeyboardMarkup(inline_keyboard=kb)


def create_admin_list_kb() -> InlineKeyboardMarkup:
    kb = []

    for fullname, user_id in DB.get_admins_fullnames_ids():
        kb.append([
            InlineKeyboardButton(
                text=f"{fullname}",
                callback_data=AdminCallbackFactory(
                    user_id=user_id,
                ).pack(),
            )
        ])

    kb.append([InlineKeyboardButton(text="➢ Назад", callback_data="go_back")])

    return InlineKeyboardMarkup(inline_keyboard=kb)


def create_places_list_kb() -> InlineKeyboardMarkup:
    kb = []

    for title, chat_id in DB.get_places():
        kb.append([
            InlineKeyboardButton(
                text=f"{title}",
                callback_data=PlaceCallbackFactory(
                    title=title,
                    chat_id=chat_id,
                ).pack(),
            )
        ])

    kb.append([InlineKeyboardButton(text="➢ Назад", callback_data="go_back")])

    return InlineKeyboardMarkup(inline_keyboard=kb)


def create_delete_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Удалить", callback_data="delete")],
            [InlineKeyboardButton(text="➢ Назад", callback_data="go_back")],
        ]
    )


def create_watching_employees_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➢ Назад", callback_data="go_back")],
        ]
    )


def create_watching_admins_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➢ Назад", callback_data="go_back")],
        ]
    )


def create_watching_places_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➢ Назад", callback_data="go_back")],
        ]
    )
