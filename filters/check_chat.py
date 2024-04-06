from aiogram.filters import BaseFilter
from aiogram.types import Message
from db import DB


class CheckChatFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return not int(message.chat.id) not in DB.get_chat_ids()