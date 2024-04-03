import asyncio
import logging
from threading import Thread
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from config.config import config
from menu_command import set_default_commands
from handlers import (
    router_authorise,
    router_start_shift,
    router_daily,
    router_finish,
    router_encashment
)
from handlers.admin_handler import router_admin
from db import DB
from lexicon.lexicon_ru import NOTIFICATION

bot = Bot(token=config.tg_bot.token)
storage = RedisStorage(redis=config.redis)
dp = Dispatcher(storage=storage)

logging.basicConfig(level=logging.INFO)


async def auto_posting():
    last_message = None

    while True:
        if datetime.now(tz=timezone(timedelta(hours=3.0))).hour == 16:
            user_ids = DB.get_users()

            for user_id in user_ids:
                if user_id[0] in config.employees:
                    try:
                        message = await bot.send_message(
                            chat_id=user_id[0],
                            text=NOTIFICATION,
                            parse_mode="html",
                        )

                        if last_message is not None:
                            await bot.delete_message(
                                chat_id=last_message.chat.id,
                                message_id=last_message.message_id,
                            )

                        last_message = message

                        await asyncio.sleep(60 * 60)
                    except Exception as e:
                        print("main.py: The user has blocked the bot:", e)
        else:
            await asyncio.sleep(60)


def creating_new_loop(global_loop):
    asyncio.run_coroutine_threadsafe(auto_posting(), global_loop)


async def main() -> None:
    # Подключаем роутеры к корневому роутеру (диспетчеру)
    dp.include_router(router_authorise)
    dp.include_router(router_start_shift)
    dp.include_router(router_daily)
    dp.include_router(router_finish)
    dp.include_router(router_encashment)
    dp.include_router(router_admin)

    await set_default_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    global_loop = asyncio.get_event_loop()
    auto_posting_thread = Thread(target=creating_new_loop, args=(global_loop,))
    auto_posting_thread.start()

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
