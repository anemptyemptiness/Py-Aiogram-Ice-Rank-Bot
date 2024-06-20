from typing import Dict, Any, Union
from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, ReplyKeyboardRemove
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError

from src.keyboards.keyboard import create_cancel_kb, create_yes_no_kb, create_places_kb
from src.fsm.fsm import FSMDailyChecking
from src.middleware.album_middleware import AlbumsMiddleware
from src.lexicon.lexicon_ru import RUSSIAN_WEEK_DAYS
from src.callbacks.place import PlaceCallbackFactory
from src.db.queries.dao.dao import AsyncOrm
from src.config import settings
from src.db import cached_places
import logging

logger = logging.getLogger(__name__)

router_daily = Router()
router_daily.message.middleware(middleware=AlbumsMiddleware(2))


async def report(dictionary: Dict[str, Any], date: str, user_id: Union[str, int]) -> str:
    return f"📔Дневная сверка:\n\n" \
           f"Дата: {date}\n" \
           f"Точка: {dictionary['place']}\n" \
           f"Имя: {await AsyncOrm.get_current_name(user_id=user_id)}\n\n" \
           f"Количество оплат равно количеству посетителей: <em>{'да' if dictionary['check_people_pays'] == 'yes' else 'нет'}</em>\n" \
           f"Есть ли дефекты у коньков: <em>{'нет' if dictionary['is_ice_rank_defects'] == 'no' else 'да⚠️'}</em>\n" \
           f"Количество проданных билетов: <em>{dictionary['count_tickets']}</em>\n" \
           f"Сумма: <em>{dictionary['summary']} <b>₽</b></em>\n\n" \
           f"Есть ли неисправности или вопросы, требующие немедленного решения: <em>{'нет' if dictionary['is_strong_defects'] == 'no' else '⚠️Нужно срочно связаться с сотрудником⚠️'}</em>\n\n" \
           f"Есть ли жалобы или предложения от посетителей: <em>{'нет' if dictionary['book_of_suggestions'] == 'no' else dictionary['book_info']}</em>"


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

        working_place = [
            InputMediaPhoto(
                media=photo_file_id,
                caption="Фото проката" if i == 0 else ""
            ) for i, photo_file_id in enumerate(data["working_place_photo"])
        ]

        await message.bot.send_media_group(
            chat_id=chat_id,
            media=working_place
        )

        if data["is_ice_rank_defects"] == "yes":
            ice_rank_defects = [
                InputMediaPhoto(
                    media=photo_file_id,
                    caption="Фото дефектов у коньков" if i == 0 else ""
                ) for i, photo_file_id in enumerate(data["defects_photo"])
            ]

            await message.bot.send_media_group(
                chat_id=chat_id,
                media=ice_rank_defects
            )

        await message.answer(
            text="Отлично! Отчёт успешно отправлен👍🏻",
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            text="Вы вернулись в главное меню"
        )

    except Exception as e:
        logger.exception("Ошибка не с телеграм в daily_checking.py при отправке отчета")
        await message.bot.send_message(
            text=f"Daily checking report error: {e}\n"
                 f"User id: {message.chat.id}",
            chat_id=settings.ADMIN_ID,
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            text="Упс... что-то пошло не так, сообщите руководству!",
            reply_markup=ReplyKeyboardRemove(),
        )
    except TelegramAPIError as e:
        logger.exception("Ошибка с телеграм в daily_checking.py при отправке отчета")
        await message.bot.send_message(
            text=f"Daily checking report error: {e}\n"
                 f"User id: {message.chat.id}",
            chat_id=settings.ADMIN_ID,
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            text="Упс... что-то пошло не так, сообщите руководству!",
            reply_markup=ReplyKeyboardRemove(),
        )
    finally:
        await state.clear()


@router_daily.message(Command(commands="daily_checking"), StateFilter(default_state))
async def process_start_daily_check_command(message: Message, state: FSMContext):
    await message.answer(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>",
        reply_markup=create_places_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMDailyChecking.place)


@router_daily.callback_query(StateFilter(FSMDailyChecking.place), PlaceCallbackFactory.filter())
async def process_place_command(callback: CallbackQuery, callback_data: PlaceCallbackFactory, state: FSMContext):
    await state.update_data(place=callback_data.title)
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>\n\n"
             f"➢ {callback_data.title}",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Количество оплат сходится с количеством посетителей?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMDailyChecking.check_people_pays)


@router_daily.callback_query(StateFilter(FSMDailyChecking.check_people_pays), F.data == "yes")
async def process_check_pays_and_people_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(check_people_pays="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Количество оплат сходится с количеством посетителей?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Отлично! Теперь нужно прислать фото проката",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMDailyChecking.working_place_photo)


@router_daily.callback_query(StateFilter(FSMDailyChecking.check_people_pays), F.data == "no")
async def process_check_pays_and_people_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(check_people_pays="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Количество оплат сходится с количеством посетителей?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="Отлично! Теперь нужно прислать фото проката",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMDailyChecking.working_place_photo)


@router_daily.message(StateFilter(FSMDailyChecking.working_place_photo))
async def process_working_place_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "working_place_photo" not in await state.get_data():
            await state.update_data(working_place_photo=[message.photo[-1].file_id])

        await message.answer(
            text="Есть ли дефекты на коньках?",
            reply_markup=create_yes_no_kb(),
        )
        await state.set_state(FSMDailyChecking.is_ice_rank_defects)
    else:
        await message.answer(
            text="Нужно прислать <b>фото</b> проката",
            reply_markup=create_cancel_kb(),
            parse_mode="html",
        )


@router_daily.callback_query(StateFilter(FSMDailyChecking.is_ice_rank_defects), F.data == "yes")
async def process_is_ice_rank_defects_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_ice_rank_defects="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли дефекты на коньках?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Пришлите фото дефектов",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMDailyChecking.defects_photo)


@router_daily.callback_query(StateFilter(FSMDailyChecking.is_ice_rank_defects), F.data == "no")
async def process_is_ice_rank_defects_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_ice_rank_defects="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли дефекты на коньках?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="Есть ли жалобы или предложения от посетителей?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMDailyChecking.book_of_suggestions)


@router_daily.message(StateFilter(FSMDailyChecking.defects_photo))
async def process_ice_rank_defects_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "defects_photo" not in await state.get_data():
            await state.update_data(defects_photo=[message.photo[-1].file_id])

        await message.answer(
            text="Есть ли жалобы или предложения от посетителей?",
            reply_markup=create_yes_no_kb(),
        )
        await state.set_state(FSMDailyChecking.book_of_suggestions)
    else:
        await message.answer(
            text="Нужно прислать <b>фото</b> дефектов",
            reply_markup=create_cancel_kb(),
            parse_mode="html",
        )


@router_daily.callback_query(StateFilter(FSMDailyChecking.book_of_suggestions), F.data == "yes")
async def process_book_sug_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(book_of_suggestions="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли жалобы или предложения от посетителей?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Напишите <b>в ОДНОМ</b> сообщении жалобы и предложения\n\n"
             "Например:\n"
             "жалобы: ...\n"
             "предложения: ...",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMDailyChecking.book_info)


@router_daily.callback_query(StateFilter(FSMDailyChecking.book_of_suggestions), F.data == "no")
async def process_book_sug_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(book_of_suggestions="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли жалобы или предложения от посетителей?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="Если ли неисправности или вопросы, требующие немедленного решения?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMDailyChecking.is_strong_defects)


@router_daily.message(StateFilter(FSMDailyChecking.book_info), F.text)
async def process_book_info_command(message: Message, state: FSMContext):
    await state.update_data(book_info='\n' + message.text)
    await message.answer(
        text="Есть ли неисправности или вопросы, требующие немедленного решения?",
        reply_markup=create_yes_no_kb(),
    )
    await state.set_state(FSMDailyChecking.is_strong_defects)


@router_daily.message(StateFilter(FSMDailyChecking.book_info))
async def warning_book_info_command(message: Message):
    await message.answer(
        text="Напишите <b>в ОДНОМ</b> сообщении жалобы и предложения\n\n"
             "Например:\n"
             "жалобы: ...\n"
             "предложения: ...",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_daily.callback_query(StateFilter(FSMDailyChecking.is_strong_defects), F.data == "yes")
async def process_is_strong_defects_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_strong_defects="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Если ли неисправности или вопросы, требующие немедленного решения?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Хорошо, я передам это начальству!",
        reply_markup=create_cancel_kb(),
    )
    await callback.message.answer(
        text="Напишите количество проданных билетов <b>числом без точки</b>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMDailyChecking.count_tickets)


@router_daily.callback_query(StateFilter(FSMDailyChecking.is_strong_defects), F.data == "no")
async def process_is_strong_defects_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_strong_defects="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Если ли неисправности или вопросы, требующие немедленного решения?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="Напишите количество проданных билетов <b>числом без любых других символов</b>\n\n"
             "<em>Например: 1</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMDailyChecking.count_tickets)


@router_daily.message(StateFilter(FSMDailyChecking.count_tickets), F.text.isdigit())
async def process_count_tickets_command(message: Message, state: FSMContext):
    await state.update_data(count_tickets=message.text)
    await message.answer(
        text="Напишите сумму, полученную с проданных билетов\n\n"
             "<em>Например: 1000</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMDailyChecking.summary)


@router_daily.message(StateFilter(FSMDailyChecking.count_tickets))
async def warning_count_tickets_command(message: Message):
    await message.answer(
        text="Напишите количество проданных билетов <b>числом без любых других символов</b>\n\n"
             "<em>Например: 1</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_daily.message(StateFilter(FSMDailyChecking.summary), F.text.isdigit())
async def process_summary_command(message: Message, state: FSMContext):
    await state.update_data(summary=message.text)

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(
        f'%d/%m/%Y - {RUSSIAN_WEEK_DAYS[day_of_week]}')

    daily_check_dict = await state.get_data()

    await send_report(
        message=message,
        state=state,
        data=daily_check_dict,
        date=current_date,
        chat_id=cached_places[daily_check_dict["place"]],
    )


@router_daily.message(StateFilter(FSMDailyChecking.summary))
async def warning_summary_command(message: Message):
    await message.answer(
        text="Напишите сумму, полученную с проданных билетов\n\n"
             "<em>Например: 1000</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
