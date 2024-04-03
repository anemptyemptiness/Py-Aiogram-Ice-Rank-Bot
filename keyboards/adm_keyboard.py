from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from callbacks.employee import EmployeeCallbackFactory
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


def create_employee_list_kb() -> InlineKeyboardMarkup:
    kb = []

    for fullname, username in DB.get_employees():
        kb.append([
            InlineKeyboardButton(
                text=f"{fullname}",
                callback_data=EmployeeCallbackFactory(
                    username=username,
                    fullname=fullname,
                ).pack(),
            )
        ])

    kb.append([InlineKeyboardButton(text="🠔 Назад", callback_data="go_back")])

    return InlineKeyboardMarkup(inline_keyboard=kb)


def create_delete_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Удалить", callback_data="delete")],
            [InlineKeyboardButton(text="🠔 Назад", callback_data="go_back")],
        ]
    )


def create_watching_employees_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🠔 Назад", callback_data="go_back")],
        ]
    )
