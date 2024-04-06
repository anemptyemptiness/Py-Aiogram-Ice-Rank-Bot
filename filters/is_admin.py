from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from db import DB


class isAdminFilterMessage(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return int(message.from_user.id) in DB.get_admins_user_ids()


class isNotAdminFilterCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return not int(callback.message.chat.id) in DB.get_admins_user_ids()
