from aiogram.filters.callback_data import CallbackData


class EmployeeCallbackFactory(CallbackData, prefix="employee"):
    username: str
    fullname: str
