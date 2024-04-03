from aiogram import types


async def set_default_commands(bot):
    await bot.set_my_commands([
        types.BotCommand(command="start_shift", description="Открыть смену"),
        types.BotCommand(command="daily_checking", description="Дневная сверка"),
        types.BotCommand(command="finish_shift", description="Закрыть смену"),
        types.BotCommand(command="encashment", description="Инкассация"),
        types.BotCommand(command="admin", description="Админка"),
    ])
