from aiogram.filters import BaseFilter
from aiogram.types import Message
from db import DB


class CheckUserFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user_id = int(message.from_user.id)
        return not (user_id in DB.get_employees_user_ids() or user_id in DB.get_admins_user_ids())