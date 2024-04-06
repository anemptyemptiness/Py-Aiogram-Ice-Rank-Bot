from aiogram.filters.callback_data import CallbackData


class AdminCallbackFactory(CallbackData, prefix="admin"):
    username: str
    fullname: str
