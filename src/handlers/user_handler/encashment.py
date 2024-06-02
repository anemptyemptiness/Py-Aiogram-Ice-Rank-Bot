from datetime import datetime, timedelta, timezone
from typing import Dict, Union, Any

from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InputMediaPhoto
from aiogram import Router, F
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.exceptions import TelegramBadRequest

from src.fsm.fsm import FSMEncashment
from src.keyboards.keyboard import create_cancel_kb, create_yes_no_kb, create_places_kb
from src.middleware.album_middleware import AlbumsMiddleware
from src.lexicon.lexicon_ru import RUSSIAN_WEEK_DAYS
from src.config import settings
from src.callbacks.place import PlaceCallbackFactory
from src.db import cached_places
from src.db.queries.dao.dao import AsyncOrm
import logging

logger = logging.getLogger(__name__)

router_encashment = Router()
router_encashment.message.middleware(middleware=AlbumsMiddleware(2))


async def report(dictionary: Dict[str, Any], date: str, user_id: Union[str, int]) -> str:
    return f"📝 Инкассация:\n\n" \
           f"Дата: {date}\n" \
           f"Точка: {dictionary['place']}\n" \
           f"Имя: {await AsyncOrm.get_current_name(user_id=user_id)}\n\n" \
           f"Сумма инкассации: <em>{dictionary['cash']}</em>\n" \
           f"Дата инкассации: <em>{dictionary['date']}</em>"


async def send_report(message: Message, state: FSMContext, data: dict, date: str, chat_id: Union[str, int]):
    try:
        await message.bot.send_message(
            chat_id=chat_id,
            text=await report(
                dictionary=data,
                date=date,
                user_id=message.chat.id,
            ),
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="html",
        )

        receipts = [
            InputMediaPhoto(
                media=photo_file_id,
                caption="Фото необходимых чеков" if i == 0 else ""
            ) for i, photo_file_id in enumerate(data["receipts_photo"])
        ]

        await message.bot.send_media_group(
            chat_id=chat_id,
            media=receipts,
        )

        await message.answer(
            text="Отлично! Отчёт успешно отправлен👍🏻",
            reply_markup=ReplyKeyboardRemove(),
        )
    except TelegramBadRequest as e:
        logger.exception("Ошибка в encashment.py при отправке отчета")
        await message.bot.send_message(
            text=f"Encashment report error: {e}\n"
                 f"User id: {message.chat.id}",
            chat_id=settings.ADMIN_ID,
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            text="Упс... что-то пошло не так, сообщите руководству!",
            reply_markup=ReplyKeyboardRemove(),
        )
    finally:
        await message.answer(
            text="Вы вернулись в главное меню"
        )
        await state.clear()


@router_encashment.message(Command(commands="encashment"), StateFilter(default_state))
async def process_start_encashment_command(message: Message, state: FSMContext):
    await message.answer(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>",
        reply_markup=create_places_kb(),
        parse_mode="html",
    )

    await state.set_state(FSMEncashment.place)


@router_encashment.callback_query(StateFilter(FSMEncashment.place), PlaceCallbackFactory.filter())
async def process_place_command(callback: CallbackQuery, callback_data: PlaceCallbackFactory, state: FSMContext):
    await state.update_data(place=callback_data.title)
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>\n\n"
             f"➢ {callback_data.title}",
        parse_mode="html",
    )
    await callback.message.answer(
        text="У вас есть инкассация за вчерашний день?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMEncashment.is_encashment)


@router_encashment.callback_query(StateFilter(FSMEncashment.is_encashment), F.data == "yes")
async def process_is_encashment_yes_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="У вас есть инкассация за вчерашний день?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Пожалуйста, сфотографируйте чек!"
    )
    await callback.answer()
    await state.set_state(FSMEncashment.receipts_photo)


@router_encashment.callback_query(StateFilter(FSMEncashment.is_encashment), F.data == "no")
async def process_is_encashment_no_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="У вас есть инкассация за вчерашний день?\n\n"
             "➢ Нет"
    )

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {RUSSIAN_WEEK_DAYS[day_of_week]}')

    encashment_dict = await state.get_data()

    try:
        await callback.message.bot.send_message(
            text="📝 Инкассация:\n\n"
                 f"Дата: {current_date}\n"
                 f"Точка: {encashment_dict['place']}\n"
                 f"Имя: {await AsyncOrm.get_current_name(user_id=callback.message.chat.id)}\n\n"
                 "⚠️Инкассации нет!",
            chat_id=cached_places[encashment_dict["place"]],
        )
        await callback.message.answer(
            text="Спасибо большое за информацию!"
        )
        await callback.message.answer(
            text="Отлично! Отчёт успешно отправлен👍🏻",
            reply_markup=ReplyKeyboardRemove(),
        )
        await callback.message.answer(
            text="Вы вернулись в главное меню"
        )
    except TelegramBadRequest as e:
        await callback.message.bot.send_message(
            text=f"Encashment report error: {e}\n"
                 f"User id: {callback.message.chat.id}",
            chat_id=settings.ADMIN_ID,
            reply_markup=ReplyKeyboardRemove(),
        )
        await callback.message.answer(
            text="Упс... что-то пошло не так, сообщите руководству!",
            reply_markup=ReplyKeyboardRemove(),
        )
    finally:
        await callback.answer()
        await state.clear()


@router_encashment.message(StateFilter(FSMEncashment.receipts_photo))
async def process_receipts_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "receipts_photo" not in await state.get_data():
            await state.update_data(receipts_photo=[message.photo[-1].file_id])

        await message.answer(
            text="Отлично, теперь напишите сумму",
            reply_markup=create_cancel_kb(),
        )
        await state.set_state(FSMEncashment.cash)
    else:
        await message.answer(
            text="Пожалуйста, пришлите фото чека!",
            reply_markup=create_cancel_kb(),
        )


@router_encashment.message(StateFilter(FSMEncashment.cash), F.text)
async def process_cash_command(message: Message, state: FSMContext):
    await state.update_data(cash=message.text)
    await message.answer(
        text="А теперь напишите дату, за которую инкассировали",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMEncashment.date)


@router_encashment.message(StateFilter(FSMEncashment.cash))
async def warning_cash_command(message: Message):
    await message.answer(
        text="Напишите сумму инкассации числом!",
        reply_markup=create_cancel_kb(),
    )


@router_encashment.message(StateFilter(FSMEncashment.date), F.text)
async def process_date_command(message: Message, state: FSMContext):
    await state.update_data(date=message.text)

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {RUSSIAN_WEEK_DAYS[day_of_week]}')

    encashment_dict = await state.get_data()

    await send_report(
        message=message,
        state=state,
        data=encashment_dict,
        date=current_date,
        chat_id=cached_places[encashment_dict["place"]],
    )


@router_encashment.message(StateFilter(FSMEncashment.date))
async def warning_date_command(message: Message):
    await message.answer(
        text="Напишите дату, за которую инкассировали!",
        reply_markup=create_cancel_kb(),
    )
