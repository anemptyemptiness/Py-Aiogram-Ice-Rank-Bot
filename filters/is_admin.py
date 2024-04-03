from aiogram.filters import BaseFilter
from aiogram.types import Message
from db import DB


class isAdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return int(message.from_user.id) in DB.get_admins()