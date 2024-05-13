from datetime import datetime, timedelta, timezone
from typing import Dict, Union, Any

from aiogram.types import Message, CallbackQuery, InputMediaPhoto, ReplyKeyboardRemove
from aiogram.filters import StateFilter, Command
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest

from keyboards.keyboard import create_places_kb, create_cancel_kb, create_yes_no_kb
from middleware.album_middleware import AlbumsMiddleware
from lexicon.lexicon_ru import RUSSIAN_WEEK_DAYS
from config.config import config
from fsm.fsm import FSMFinishShift
from callbacks.place import PlaceCallbackFactory
from db import DB

router_finish = Router()
router_finish.message.middleware(middleware=AlbumsMiddleware(2))
place_chat: dict = {title: chat_id for title, chat_id in DB.get_places_chat_ids()}


async def report(dictionary: Dict[str, Any], date: str, user_id: Union[str, int]) -> str:
    return f"📝Закрытие смены:\n\n" \
           f"Дата: {date}\n" \
           f"Точка: {dictionary['place']}\n" \
           f"Имя: {DB.get_current_name(user_id=user_id)}\n\n" \
           f"Произведена дезинфекция: <em>{'да' if dictionary['is_disinfection'] == 'yes' else 'нет⚠️'}</em>\n" \
           f"Коньки на сушке: <em>{'да' if dictionary['ice_rank_on_drying'] == 'yes' else 'нет⚠️'}</em>\n" \
           f"Есть ли дефекты у коньков: <em>{'да⚠️' if dictionary['is_ice_rank_defects'] == 'yes' else 'нет'}</em>\n" \
           f"Есть ли одноразовые носки и шапочки: <em>{'да' if dictionary['is_hats_and_socks'] == 'yes' else 'нет⚠️'}</em>\n" \
           f"Есть ли дефекты у защиты или шлемов: <em>{'да⚠️' if dictionary['is_depend_defects'] == 'yes' else 'нет'}</em>\n" \
           f"Музыка выключена: <em>{'да' if dictionary['is_music'] == 'yes' else 'нет⚠️'}</em>\n" \
           f"Оповещения выключены: <em>{'да' if dictionary['is_alert_off'] == 'yes' else 'нет⚠️'}</em>\n\n" \
           f"Наличные: <em>{dictionary['cash']} руб.</em>\n" \
           f"Безнал: <em>{dictionary['online_cash']} руб.</em>\n" \
           f"QR-код: <em>{dictionary['qr_code']} руб.</em>\n" \
           f"Суммарно денег: <em>{dictionary['summary']} руб.</em>\n\n" \
           f"Число посетителей: <em>{dictionary['visitors']}</em>\n" \
           f"Льготники: <em>{'были, но <b>нет фотографий льгот</b>' if dictionary['benefits_photo'] == 'no' else 'фото ниже'}</em>"


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

        if "receipts_photo" in data:
            receipts = [
                InputMediaPhoto(
                    media=photo_file_id,
                    caption="Необходимые чеки" if i == 0 else ""
                ) for i, photo_file_id in enumerate(data["receipts_photo"])
            ]

            await message.bot.send_media_group(
                chat_id=chat_id,
                media=receipts,
            )

        if data["is_benefits"] == "yes":
            if "benefits_photo" in data:
                if data["benefits_photo"] != "no":
                    benefits = [
                        InputMediaPhoto(
                            media=photo_file_id,
                            caption="Льготники" if i == 0 else ""
                        ) for i, photo_file_id in enumerate(data["benefits_photo"])
                    ]

                    await message.bot.send_media_group(
                        chat_id=chat_id,
                        media=benefits,
                    )

        if data["is_ice_rank_defects"] == "yes":
            ice_rank_defects = [
                InputMediaPhoto(
                    media=photo_file_id,
                    caption="Дефекты у коньков" if i == 0 else ""
                ) for i, photo_file_id in enumerate(data["defects_photo"])
            ]

            await message.bot.send_media_group(
                chat_id=chat_id,
                media=ice_rank_defects,
            )

        if data["is_depend_defects"] == "yes":
            depend_defects = [
                InputMediaPhoto(
                    media=photo_file_id,
                    caption="Дефекты защиты и шлемов" if i == 0 else ""
                ) for i, photo_file_id in enumerate(data["depend_defects_photo"])
            ]

            await message.bot.send_media_group(
                chat_id=chat_id,
                media=depend_defects,
            )

        await message.answer(
            text="Отлично! Отчёт успешно отправлен👍🏻",
            reply_markup=ReplyKeyboardRemove(),
        )

    except TelegramBadRequest as e:
        await message.bot.send_message(
            text=f"Finish shift report error: {e}\n"
                 f"User id: {message.chat.id}",
            chat_id=config.admin,
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


@router_finish.message(Command(commands="finish_shift"), StateFilter(default_state))
async def process_start_finish_shift_command(message: Message, state: FSMContext):
    await message.answer(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>",
        reply_markup=create_places_kb(),
        parse_mode="html",
    )

    await state.set_state(FSMFinishShift.place)


@router_finish.callback_query(StateFilter(FSMFinishShift.place), PlaceCallbackFactory.filter())
async def process_place_command(callback: CallbackQuery, callback_data: PlaceCallbackFactory, state: FSMContext):
    await state.update_data(place=callback_data.title)
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>\n\n"
             f"➢ {callback_data.title}",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Пожалуйста, введите количество посетителей <b>числом</b>\n\n"
             "<em>Например: 20</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.visitors)


@router_finish.message(StateFilter(FSMFinishShift.visitors), F.text.isdigit())
async def process_visitors_command(message: Message, state: FSMContext):
    await state.update_data(visitors=int(message.text))
    await message.answer(
        text="Введите суммарное количество наличными за сегодня <b>числом</b>\n\n"
             "<em>Например: 1000</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMFinishShift.cash)


@router_finish.message(StateFilter(FSMFinishShift.visitors))
async def warning_visitors_command(message: Message):
    await message.answer(
        text="Введите количество посетителей за день <b>числом</b>!\n\n"
             "<em>Например: 20</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_finish.message(StateFilter(FSMFinishShift.cash), F.text)
async def process_cash_command(message: Message, state: FSMContext):
    await state.update_data(cash=message.text)
    await message.answer(
        text="Введите суммарное количество безнала за сегодня <b>числом</b>\n\n"
             "<em>Например: 1000</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMFinishShift.online_cash)


@router_finish.message(StateFilter(FSMFinishShift.cash))
async def warning_cash_command(message: Message):
    await message.answer(
        text="Введите суммарное количество наличных за сегодня <b>числом без каких-либо других символов</b>\n\n"
             "<em>Например: 1000</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_finish.message(StateFilter(FSMFinishShift.online_cash), F.text)
async def process_online_cash_command(message: Message, state: FSMContext):
    await state.update_data(online_cash=message.text)
    await message.answer(
        text="Введите суммарное количество денег по qr-коду за сегодня <b>числом</b>\n\n"
             "<em>Например: 1000</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMFinishShift.qr_code)


@router_finish.message(StateFilter(FSMFinishShift.online_cash))
async def warning_online_cash_command(message: Message):
    await message.answer(
        text="Введите суммарное количество безнала за сегодня <b>числом без каких-либо других символов</b>\n\n"
             "<em>Например: 1000</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_finish.message(StateFilter(FSMFinishShift.qr_code), F.text)
async def process_qr_code_command(message: Message, state: FSMContext):
    await state.update_data(qr_code=message.text)
    await message.answer(
        text="Введите общую сумму выручки за сегодня <b>числом</b>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMFinishShift.summary)


@router_finish.message(StateFilter(FSMFinishShift.qr_code))
async def warning_qr_code_command(message: Message):
    await message.answer(
        text="Введите суммарное количество денег по qr-коду за сегодня <b>числом без каких-либо других символов</b>\n\n"
             "<em>Например: 1000</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_finish.message(StateFilter(FSMFinishShift.summary), F.text.isdigit())
async def process_summary_command(message: Message, state: FSMContext):
    await state.update_data(summary=float(message.text))
    await message.answer(
        text="Пожалуйста, пришлите фото всех необходимых чеков",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.receipts_photo)


@router_finish.message(StateFilter(FSMFinishShift.summary))
async def warning_summary_command(message: Message):
    await message.answer(
        text="Введите общую сумму выручки за сегодня <b>числом</b>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_finish.message(StateFilter(FSMFinishShift.receipts_photo))
async def process_receipts_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "receipts_photo" not in await state.get_data():
            await state.update_data(receipts_photo=[message.photo[-1].file_id])

        await message.answer(
            text="Были ли льготники сегодня?",
            reply_markup=create_yes_no_kb(),
        )
        await state.set_state(FSMFinishShift.is_benefits)
    else:
        await message.answer(
            text="Пожалуйста, пришлите фото всех необходимых чеков",
            reply_markup=create_cancel_kb(),
        )


@router_finish.callback_query(StateFilter(FSMFinishShift.is_benefits), F.data == "yes")
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
    await state.set_state(FSMFinishShift.benefits_photo)


@router_finish.callback_query(StateFilter(FSMFinishShift.is_benefits), F.data == "no")
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


@router_finish.message(StateFilter(FSMFinishShift.benefits_photo))
async def process_benefits_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "benefits_photo" not in await state.get_data():
            await state.update_data(benefits_photo=[message.photo[-1].file_id])

        await message.answer(
            text="Дезинфекция произведена?",
            reply_markup=create_yes_no_kb(),
        )
        await state.set_state(FSMFinishShift.is_disinfection)
    elif message.text.lower() == "нет фото":
        await state.update_data(benefits_photo="no")
        await message.answer(
            text="Дезинфекция произведена?",
            reply_markup=create_yes_no_kb(),
        )
        await state.set_state(FSMFinishShift.is_disinfection)
    else:
        await message.answer(
            text="Пожалуйста, пришлите фото льготных удостоверений\n\n"
                 'Если фотографий нет, то напишите <b>"нет фото"</b>',
            reply_markup=create_cancel_kb(),
            parse_mode="html",
        )


@router_finish.callback_query(StateFilter(FSMFinishShift.is_disinfection), F.data == "yes")
async def process_is_disinfection_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_disinfection="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Дезинфекция произведена?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Коньки на сушке?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.ice_rank_on_drying)


@router_finish.callback_query(StateFilter(FSMFinishShift.is_disinfection), F.data == "no")
async def process_is_disinfection_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_disinfection="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Дезинфекция произведена?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="Коньки на сушке?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.ice_rank_on_drying)


@router_finish.callback_query(StateFilter(FSMFinishShift.ice_rank_on_drying), F.data == "yes")
async def process_ice_rank_drying_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(ice_rank_on_drying="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Коньки на сушке?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Есть ли дефекты у коньков?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.is_ice_rank_defects)


@router_finish.callback_query(StateFilter(FSMFinishShift.ice_rank_on_drying), F.data == "no")
async def process_ice_rank_drying_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(ice_rank_on_drying="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Коньки на сушке?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="Есть ли дефекты у коньков?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.is_ice_rank_defects)


@router_finish.callback_query(StateFilter(FSMFinishShift.is_ice_rank_defects), F.data == "yes")
async def process_is_ice_rank_defects_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_ice_rank_defects="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли дефекты у коньков?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Пожалуйста, пришлите фото дефектов",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.defects_photo)


@router_finish.callback_query(StateFilter(FSMFinishShift.is_ice_rank_defects), F.data == "no")
async def process_is_ice_rank_defects_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_ice_rank_defects="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли дефекты у коньков?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="Есть ли одноразовые носки и шапочки?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.is_hats_and_socks)


@router_finish.message(StateFilter(FSMFinishShift.defects_photo))
async def process_defects_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "defects_photo" not in await state.get_data():
            await state.update_data(defects_photo=[message.photo[-1].file_id])

        await message.answer(
            text="Есть ли одноразовые носки и шапочки?",
            reply_markup=create_yes_no_kb(),
        )
        await state.set_state(FSMFinishShift.is_hats_and_socks)
    else:
        await message.answer(
            text="Пожалуйста, пришлите <b>фото</b> дефектов",
            reply_markup=create_cancel_kb(),
            parse_mode="html",
        )


@router_finish.callback_query(StateFilter(FSMFinishShift.is_hats_and_socks), F.data == "yes")
async def process_is_hats_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_hats_and_socks="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли одноразовые носки и шапочки?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Есть ли дефекты защиты или шлемов?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.is_depend_defects)


@router_finish.callback_query(StateFilter(FSMFinishShift.is_hats_and_socks), F.data == "no")
async def process_is_hats_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_hats_and_socks="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли одноразовые носки и шапочки?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="Есть ли дефекты защиты или шлемов?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.is_depend_defects)


@router_finish.callback_query(StateFilter(FSMFinishShift.is_depend_defects), F.data == "yes")
async def process_is_depend_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_depend_defects="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли дефекты защиты или шлемов?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Пожалуйста, пришлите фото дефектов",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.depend_defects_photo)


@router_finish.callback_query(StateFilter(FSMFinishShift.is_depend_defects), F.data == "no")
async def process_is_depend_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_depend_defects="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли дефекты защиты или шлемов?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="Музыка выключена?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.is_music)


@router_finish.message(StateFilter(FSMFinishShift.depend_defects_photo))
async def process_depend_defects_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "depend_defects_photo" not in await state.get_data():
            await state.update_data(depend_defects_photo=[message.photo[-1].file_id])

        await message.answer(
            text="Музыка выключена?",
            reply_markup=create_yes_no_kb(),
        )
        await state.set_state(FSMFinishShift.is_music)
    else:
        await message.answer(
            text="Пожалуйста, пришлите фото дефектов",
            reply_markup=create_cancel_kb(),
        )


@router_finish.callback_query(StateFilter(FSMFinishShift.is_music), F.data == "yes")
async def process_is_music_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_music="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Музыка выключена?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Оповещения выключены?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.is_alert_off)


@router_finish.callback_query(StateFilter(FSMFinishShift.is_music), F.data == "no")
async def process_is_music_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_music="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Музыка выключена?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="Оповещения выключены?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.is_alert_off)


@router_finish.callback_query(StateFilter(FSMFinishShift.is_alert_off), F.data == "yes")
async def process_is_alert_off_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_alert_off="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Оповещения выключены?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Павильон закрыт?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.is_working_place_closed)


@router_finish.callback_query(StateFilter(FSMFinishShift.is_alert_off), F.data == "no")
async def process_is_alert_off_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_alert_off="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Оповещения выключены?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="Павильон закрыт?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.is_working_place_closed)


@router_finish.callback_query(StateFilter(FSMFinishShift.is_working_place_closed), F.data == "yes")
async def process_working_place_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_working_place_closed="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Павильон закрыт?\n\n"
             "➢ Да"
    )

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {RUSSIAN_WEEK_DAYS[day_of_week]}')

    finish_shift_dict = await state.get_data()

    await send_report(
        message=callback.message,
        state=state,
        data=finish_shift_dict,
        date=current_date,
        chat_id=place_chat[finish_shift_dict["place"]],
    )

    await callback.answer()


@router_finish.callback_query(StateFilter(FSMFinishShift.is_working_place_closed), F.data == "no")
async def process_working_place_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_working_place_closed="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Павильон закрыт?\n\n"
             "➢ Нет"
    )

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {RUSSIAN_WEEK_DAYS[day_of_week]}')

    finish_shift_dict = await state.get_data()

    await send_report(
        message=callback.message,
        state=state,
        data=finish_shift_dict,
        date=current_date,
        chat_id=place_chat[finish_shift_dict["place"]],
    )

    await callback.answer()
