from datetime import datetime, timezone, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from db import cached_employees
from lexicon.lexicon_ru import NOTIFICATION
import asyncio
import logging

logger = logging.getLogger(__name__)


def creating_new_loop_for_notification(global_loop, bot: Bot):
    asyncio.run_coroutine_threadsafe(auto_posting(bot), global_loop)


async def auto_posting(bot: Bot):
    last_message = None

    while True:
        if datetime.now(tz=timezone(timedelta(hours=3.0))).hour == 16:
            user_ids = cached_employees

            if not user_ids:
                await asyncio.sleep(60 * 60)  # спим час

            for user_id in user_ids:
                try:
                    message = await bot.send_message(
                        chat_id=user_id,
                        text=NOTIFICATION,
                        parse_mode="html",
                    )

                    if last_message is not None:
                        await bot.delete_message(
                            chat_id=last_message.chat.id,
                            message_id=last_message.message_id,
                        )

                    last_message = message

                    await asyncio.sleep(60 * 60)  # спим час
                except Exception:
                    logger.exception("Ошибка в отправке уведомлений, auto_posting()")
                except TelegramBadRequest:
                    logger.exception("Ошибка от Telegram в отправке уведомлений, auto_posting()")
        else:
            await asyncio.sleep(60 * 60)  # спим час
