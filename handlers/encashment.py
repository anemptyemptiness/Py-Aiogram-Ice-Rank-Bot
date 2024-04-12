from datetime import datetime, timedelta, timezone
from typing import Dict, Union, Any

from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InputMediaPhoto
from aiogram import Router, F
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.exceptions import TelegramBadRequest

from fsm.fsm import FSMEncashment
from keyboards.keyboard import create_cancel_kb, create_yes_no_kb, create_places_kb
from middleware.album_middleware import AlbumsMiddleware
from lexicon.lexicon_ru import RUSSIAN_WEEK_DAYS
from config.config import config
from callbacks.place import PlaceCallbackFactory
from db import DB

router_encashment = Router()
router_encashment.message.middleware(middleware=AlbumsMiddleware(2))
place_chat: dict = {title: chat_id for title, chat_id in DB.get_places_chat_ids()}


async def report(dictionary: Dict[str, Any], date: str, user_id: Union[str, int]) -> str:
    return f"📝 Инкассация:\n\n" \
           f"Дата: {date}\n" \
           f"Точка: {dictionary['place']}\n" \
           f"Имя: {DB.get_current_name(user_id=user_id)}\n\n" \
           f"Наличные: <em>{dictionary['cash']}</em>\n" \
           f"Безнал: <em>{dictionary['online_cash']}</em>\n" \
           f"QR-код: <em>{dictionary['qr_code']}</em>\n\n" \
           f"Общая сумма: <em>{dictionary['summary']}</em>\n\n" \
           f"Были ли льготники: <em>{'нет' if dictionary['is_benefits'] == 'no' else 'да'}</em>\n" \
           f"Есть ли фото льготных удостоверений: <em>{'нет' if 'benefits_photo' in dictionary and dictionary['benefits_photo'] == 'нет фото' or 'benefits_photo' not in dictionary else 'да'}</em>"


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

        if data["is_benefits"] == "yes" and "benefits_photo" in data:
            benefits = [
                InputMediaPhoto(
                    media=photo_file_id,
                    caption="Фото льготных удостоверений" if i == 0 else ""
                ) for i, photo_file_id in enumerate(data["benefits_photo"])
            ]

            await message.bot.send_media_group(
                chat_id=chat_id,
                media=benefits,
            )

        await message.answer(
            text="Отлично! Отчёт успешно отправлен👍🏻",
            reply_markup=ReplyKeyboardRemove(),
        )
    except TelegramBadRequest as e:
        await message.bot.send_message(
            text=f"Encashment report error: {e}\n"
                 f"User id: {message.chat.id}",
            chat_id=292972814,
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
        text="Введите суммарное количество наличных за сегодня <b>числом</b>\n\n"
             "<em>Например: 1000</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMEncashment.cash)


@router_encashment.message(StateFilter(FSMEncashment.cash), F.text)
async def process_cash_command(message: Message, state: FSMContext):
    await state.update_data(cash=message.text)
    await message.answer(
        text="Введите суммарное количество безнала за сегодня <b>числом</b>\n\n"
             "<em>Например: 1000</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMEncashment.online_cash)


@router_encashment.message(StateFilter(FSMEncashment.cash))
async def warning_cash_command(message: Message):
    await message.answer(
        text="Введите суммарное количество наличных за сегодня <b>числом без каких-либо других символов</b>\n\n"
             "<em>Например: 1000</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_encashment.message(StateFilter(FSMEncashment.online_cash), F.text)
async def process_online_cash_command(message: Message, state: FSMContext):
    await state.update_data(online_cash=message.text)
    await message.answer(
        text="Введите суммарное количество денег по qr-коду за сегодня <b>числом</b>\n\n"
             "<em>Например: 1000</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMEncashment.qr_code)


@router_encashment.message(StateFilter(FSMEncashment.online_cash))
async def warning_online_cash_command(message: Message):
    await message.answer(
        text="Введите суммарное количество безнала за сегодня <b>числом без каких-либо других символов</b>\n\n"
             "<em>Например: 1000</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_encashment.message(StateFilter(FSMEncashment.qr_code), F.text)
async def process_qr_code_command(message: Message, state: FSMContext):
    await state.update_data(qr_code=message.text)
    await message.answer(
        text="Введите общую сумму выручки за сегодня <b>числом</b>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMEncashment.summary)


@router_encashment.message(StateFilter(FSMEncashment.qr_code))
async def warning_qr_code_command(message: Message):
    await message.answer(
        text="Введите суммарное количество денег по qr-коду за сегодня <b>числом без каких-либо других символов</b>\n\n"
             "<em>Например: 1000</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_encashment.message(StateFilter(FSMEncashment.summary), F.text)
async def process_summary_command(message: Message, state: FSMContext):
    await state.update_data(summary=message.text)
    await message.answer(
        text="Пожалуйста, пришлите фото всех необходимых чеков",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMEncashment.receipts_photo)


@router_encashment.message(StateFilter(FSMEncashment.summary))
async def warning_summary_command(message: Message):
    await message.answer(
        text="Введите общую сумму выручки за сегодня <b>числом</b>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_encashment.message(StateFilter(FSMEncashment.receipts_photo))
async def process_receipts_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "receipts_photo" not in await state.get_data():
            await state.update_data(receipts_photo=[message.photo[-1].file_id])

        await message.answer(
            text="Были ли льготники сегодня?",
            reply_markup=create_yes_no_kb(),
        )
        await state.set_state(FSMEncashment.is_benefits)
    else:
        await message.answer(
            text="Пожалуйста, пришлите фото всех необходимых чеков",
            reply_markup=create_cancel_kb(),
        )


@router_encashment.callback_query(StateFilter(FSMEncashment.is_benefits), F.data == "yes")
async def process_benefits_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_benefits="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Были ли льготники сегодня?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Пожалуйста, пришлите фото льготных удостоверений\n\n"
             'Если фотографий нет, то напишите <b>"нет фото"</b>',
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMEncashment.benefits_photo)


@router_encashment.callback_query(StateFilter(FSMEncashment.is_benefits), F.data == "no")
async def process_benefits_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_benefits="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Были ли льготники сегодня?\n\n"
             "➢ Нет"
    )
    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {RUSSIAN_WEEK_DAYS[day_of_week]}')

    encashment_dict = await state.get_data()

    await send_report(
        message=callback.message,
        state=state,
        data=encashment_dict,
        date=current_date,
        chat_id=place_chat[encashment_dict["place"]],
    )

    await callback.answer()


@router_encashment.message(StateFilter(FSMEncashment.benefits_photo))
async def process_benefits_photo_command(message: Message, state: FSMContext):
    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {RUSSIAN_WEEK_DAYS[day_of_week]}')

    if message.photo:
        if "benefits_photo" not in await state.get_data():
            await state.update_data(benefits_photo=[message.photo[-1].file_id])

        encashment_dict = await state.get_data()

        await send_report(
            message=message,
            state=state,
            data=encashment_dict,
            date=current_date,
            chat_id=place_chat[encashment_dict["place"]],
        )

    elif message.text.lower() == "нет фото":
        encashment_dict = await state.get_data()

        await send_report(
            message=message,
            state=state,
            data=encashment_dict,
            date=current_date,
            chat_id=place_chat[encashment_dict["place"]],
        )
    else:
        await message.answer(
            text="Пожалуйста, пришлите фото льготных удостоверений\n\n"
                 'Если фотографий нет, то напишите <b>"нет фото"</b>',
            reply_markup=create_cancel_kb(),
            parse_mode="html",
        )
