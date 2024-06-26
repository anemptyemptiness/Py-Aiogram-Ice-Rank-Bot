from typing import Dict, Any, Union
from datetime import datetime, timezone, timedelta

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, InputMediaPhoto, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError

from src.fsm.fsm import FSMStartShift
from src.keyboards.keyboard import create_yes_no_kb, create_cancel_kb, create_places_kb, create_good_or_bad_kb
from src.middleware.album_middleware import AlbumsMiddleware
from src.lexicon.lexicon_ru import RUSSIAN_WEEK_DAYS
from src.config import settings
from src.callbacks.place import PlaceCallbackFactory
from src.db import cached_places
from src.db.queries.dao.dao import AsyncOrm
import logging

logger = logging.getLogger(__name__)

router_start_shift = Router()
router_start_shift.message.middleware(middleware=AlbumsMiddleware(2))


async def report(dictionary: Dict[str, Any], date: str, user_id: Union[str, int]) -> str:
    return "📝Открытие смены:\n\n" \
           f"Дата: {date}\n" \
           f"Точка: {dictionary['place']}\n" \
           f"Имя: {await AsyncOrm.get_current_name(user_id=user_id)}\n\n" \
           f"Есть дефекты у коньков: <em>{'нет' if dictionary['is_defects'] == 'no' else 'да⚠️'}</em>\n" \
           f"Все шнурки заправлены: <em>{'да' if dictionary['laces'] == 'yes' else 'no⚠️'}</em>\n" \
           f"Есть одноразовые шапочки и носки: <em>{'да' if dictionary['hats_and_socks'] == 'yes' else 'нет⚠️'}</em>\n" \
           f"Есть дефекты у пингвинов: <em>{'нет' if dictionary['is_penguins'] == 'no' else 'да⚠️'}</em>\n" \
           f"Есть дефекты ящиков хранения: <em>{'нет' if dictionary['is_boxes'] == 'no' else 'да⚠️'}</em>\n" \
           f"Музыка включена: <em>{'да' if dictionary['is_music'] == 'yes' else 'нет⚠️'}</em>\n" \
           f"Павильон и зона проката чистые: <em>{'да' if dictionary['is_clear_zone_of_ice'] == 'yes' else 'нет⚠️'}</em>\n" \
           f"Состояние льда: <em>{'хорошее🟢' if dictionary['what_state_of_ice'] == 'good' else 'плохое🔴'}</em>"


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

        await message.bot.send_photo(
            chat_id=chat_id,
            photo=data["employee_photo"],
            caption="Фото сотрудника",
        )

        # фото павильона (рабочее место)
        if data["working_place_photo"]:
            working_place_photos = [
                InputMediaPhoto(
                    media=photo_file_id,
                    caption="Фото рабочего места" if i == 0 else ""
                ) for i, photo_file_id in enumerate(data["working_place_photo"])
            ]

            await message.bot.send_media_group(
                chat_id=chat_id,
                media=working_place_photos
            )

        # фото раздевалки
        if data["cloakroom_photo"]:
            working_place_photos = [
                InputMediaPhoto(
                    media=photo_file_id,
                    caption="Фото раздевалки" if i == 0 else ""
                ) for i, photo_file_id in enumerate(data["cloakroom_photo"])
            ]

            await message.bot.send_media_group(
                chat_id=chat_id,
                media=working_place_photos
            )

        if data["is_defects"] == "yes":
            ice_rank_defects = [
                InputMediaPhoto(
                    media=photo_file_id,
                    caption="Фото дефектов у коньков" if i == 0 else ""
                ) for i, photo_file_id in enumerate(data["defects_photo"])
            ]

            await message.bot.send_media_group(
                chat_id=chat_id,
                media=ice_rank_defects,
            )

        if data["is_penguins"] == "yes":
            penguins_defects = [
                InputMediaPhoto(
                    media=photo_file_id,
                    caption="Фото дефектов у пингвинов" if i == 0 else ""
                ) for i, photo_file_id in enumerate(data["penguins_defects_photo"])
            ]

            await message.bot.send_media_group(
                chat_id=chat_id,
                media=penguins_defects,
            )

        if data["is_boxes"] == "yes":
            boxes_defects = [
                InputMediaPhoto(
                    media=photo_file_id,
                    caption="Фото дефектов ящиков хранения" if i == 0 else ""
                ) for i, photo_file_id in enumerate(data["boxes_defects_photo"])
            ]

            await message.bot.send_media_group(
                chat_id=chat_id,
                media=boxes_defects,
            )

        await message.answer(
            text="Отлично! Отчёт успешно отправлен👍🏻",
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            text="Вы вернулись в главное меню",
        )

    except Exception as e:
        logger.exception("Ошибка не с телеграм в start_shift.py при отправке отчета")
        await message.bot.send_message(
            text=f"Start shift report error: {e}\n"
                 f"User id: {message.chat.id}",
            chat_id=settings.ADMIN_ID,
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            text="Упс... что-то пошло не так, сообщите руководству!",
            reply_markup=ReplyKeyboardRemove(),
        )
    except TelegramAPIError as e:
        logger.exception("Ошибка с телеграм в start_shift.py при отправке отчета")
        await message.bot.send_message(
            text=f"Start shift report error: {e}\n"
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


@router_start_shift.message(Command(commands="start_shift"), StateFilter(default_state))
async def process_start_shift_command(message: Message, state: FSMContext):
    await message.answer(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>",
        reply_markup=create_places_kb(),
        parse_mode="html",
    )

    await state.set_state(FSMStartShift.place)


@router_start_shift.callback_query(StateFilter(FSMStartShift.place), PlaceCallbackFactory.filter())
async def process_place_command(callback: CallbackQuery, callback_data: PlaceCallbackFactory, state: FSMContext):
    await state.update_data(place=callback_data.title)
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>\n\n"
             f"➢ {callback_data.title}",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Пожалуйста, сделайте Ваше фото на рабочем месте",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.employee_photo)


@router_start_shift.message(StateFilter(FSMStartShift.employee_photo))
async def process_employee_photo_command(message: Message, state: FSMContext):
    if message.photo:
        await state.update_data(employee_photo=message.photo[-1].file_id)
        await message.answer(
            text="Отлично! Теперь нужно прислать фото павильона проката",
            reply_markup=create_cancel_kb(),
        )
        await state.set_state(FSMStartShift.working_place_photo)
    else:
        await message.answer(
            text="Нужно прислать Ваше <b>фото</b>",
            reply_markup=create_cancel_kb(),
        )


@router_start_shift.message(StateFilter(FSMStartShift.working_place_photo))
async def process_working_place_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "working_place_photo" not in await state.get_data():
            await state.update_data(working_place_photo=[message.photo[-1].file_id])

        await message.answer(
            text="Отлично! Теперь нужно отправить фото раздевалки",
            reply_markup=create_cancel_kb(),
        )
        await state.set_state(FSMStartShift.cloakroom_photo)
    else:
        await message.answer(
            text="Нужно прислать <b>фото</b> павильона",
            reply_markup=create_cancel_kb(),
            parse_mode="html",
        )


@router_start_shift.message(StateFilter(FSMStartShift.cloakroom_photo))
async def process_cloakroom_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "cloakroom_photo" not in await state.get_data():
            await state.update_data(cloakroom_photo=[message.photo[-1].file_id])

        await message.answer(
            text="Вы перенесли коньки с сушилки?",
            reply_markup=create_yes_no_kb(),
        )
        await state.set_state(FSMStartShift.ice_rank_is_dry)
    else:
        await message.answer(
            text="Нужно прислать <b>фото</b> раздевалки",
            reply_markup=create_cancel_kb(),
            parse_mode="html",
        )


@router_start_shift.callback_query(StateFilter(FSMStartShift.ice_rank_is_dry), F.data == "yes")
async def process_ice_rank_is_dry_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(ice_rank_is_dry="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Вы перенесли коньки с сушилки?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Есть ли дефекты на коньках?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.is_defects)


@router_start_shift.callback_query(StateFilter(FSMStartShift.ice_rank_is_dry), F.data == "no")
async def process_ice_rank_is_dry_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(ice_rank_is_dry="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Вы перенесли коньки с сушилки?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="⚠️Перенесите коньки с сушилки!\n\n"
             "Есть ли дефекты на коньках?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.is_defects)


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_defects), F.data == "yes")
async def process_is_defects_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_defects="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли дефекты на коньках?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Пожалуйста, сфотографируйте все дефекты и пришлите фото в ответном сообщении",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.defects_photo)


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_defects), F.data == "no")
async def process_is_defects_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_defects="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли дефекты на коньках?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="Все шнурки заправлены?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.laces)


@router_start_shift.message(StateFilter(FSMStartShift.defects_photo))
async def process_ice_rank_defects_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "defects_photo" not in await state.get_data():
            await state.update_data(defects_photo=[message.photo[-1].file_id])

        await message.answer(
            text="Все шнурки заправлены?",
            reply_markup=create_yes_no_kb(),
        )
        await state.set_state(FSMStartShift.laces)
    else:
        await message.answer(
            text="Пожалуйста, отправьте фотографии дефектов",
            reply_markup=create_cancel_kb(),
        )


@router_start_shift.callback_query(StateFilter(FSMStartShift.laces), F.data == "yes")
async def process_laces_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(laces="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Все шнурки заправлены?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Есть ли одноразовые шапочки и носки?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.hats_and_socks)


@router_start_shift.callback_query(StateFilter(FSMStartShift.laces), F.data == "no")
async def process_laces_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(laces="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Все шнурки заправлены?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="⚠️Заправьте шнурки!\n\n"
             "Есть ли одноразовые шапочки и носки?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.hats_and_socks)


@router_start_shift.callback_query(StateFilter(FSMStartShift.hats_and_socks), F.data == "yes")
async def process_hats_socks_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(hats_and_socks="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли одноразовые шапочки и носки?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Есть ли дефекты на пингвинах?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.is_penguins)


@router_start_shift.callback_query(StateFilter(FSMStartShift.hats_and_socks), F.data == "no")
async def process_hats_socks_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(hats_and_socks="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли одноразовые шапочки и носки?\n\n"
             "➢ Нет\n\n"
             "⚠️Пожалуйста, <b>срочно</b> уведомите начальство!⚠️",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Есть ли дефекты на пингвинах?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.is_penguins)


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_penguins), F.data == "yes")
async def process_penguins_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_penguins="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли дефекты на пингвинах?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Пожалуйста, пришлите фотографии дефектов",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.penguins_defects_photo)


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_penguins), F.data == "no")
async def process_penguins_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_penguins="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли дефекты на пингвинах?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="Есть ли дефекты у ящиков хранения?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.is_boxes)


@router_start_shift.message(StateFilter(FSMStartShift.penguins_defects_photo))
async def process_penguins_defects_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "penguins_defects_photo" not in await state.get_data():
            await state.update_data(penguins_defects_photo=[message.photo[-1].file_id])

        await message.answer(
            text="Есть ли дефекты у ящиков хранения?",
            reply_markup=create_yes_no_kb(),
        )
        await state.set_state(FSMStartShift.is_boxes)
    else:
        await message.answer(
            text="Пожалуйста, пришлите фото дефектов",
            reply_markup=create_cancel_kb(),
        )


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_boxes), F.data == "yes")
async def process_is_boxes_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_boxes="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли дефекты у ящиков хранения?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Пожалуйста, пришлите фотографии дефектов",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.boxes_defects_photo)


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_boxes), F.data == "no")
async def process_is_boxes_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_boxes="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли дефекты у ящиков хранения?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="Есть ли шлема и защита?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.is_defend)


@router_start_shift.message(StateFilter(FSMStartShift.boxes_defects_photo))
async def process_boxes_defects_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "boxes_defects_photo" not in await state.get_data():
            await state.update_data(boxes_defects_photo=[message.photo[-1].file_id])

        await message.answer(
            text="Есть ли шлема и защита?",
            reply_markup=create_yes_no_kb(),
        )
        await state.set_state(FSMStartShift.is_defend)
    else:
        await message.answer(
            text="Пожалуйста, пришлите фото дефектов",
            reply_markup=create_cancel_kb(),
        )


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_defend), F.data == "yes")
async def process_defend_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_defend="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли шлема и защита?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Музыка включена?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.is_music)


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_defend), F.data == "no")
async def process_defend_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_defend="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли шлема и защита?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="Музыка включена?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.is_music)


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_music), F.data == "yes")
async def process_music_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_music="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Музыка включена?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Павильон и зона проката чистые?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.is_clear_zone_of_ice)


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_music), F.data == "no")
async def process_music_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_music="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Музыка включена?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="⚠️Включите музыку!\n\n"
             "Павильон и зона проката чистые?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.is_clear_zone_of_ice)


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_clear_zone_of_ice), F.data == "yes")
async def process_is_alert_yes_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_clear_zone_of_ice="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Павильон и зона проката чистые?\n\n"
             "➢ Да"
    )
    await callback.message.answer(
        text="Каково состояние льда?",
        reply_markup=create_good_or_bad_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.what_state_of_ice)


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_clear_zone_of_ice), F.data == "no")
async def process_is_alert_no_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_clear_zone_of_ice="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Павильон и зона проката чистые?\n\n"
             "➢ Нет"
    )
    await callback.message.answer(
        text="Каково состояние льда?",
        reply_markup=create_good_or_bad_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.what_state_of_ice)


@router_start_shift.callback_query(StateFilter(FSMStartShift.what_state_of_ice), F.data == "good")
async def process_what_state_of_ice_good_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(what_state_of_ice="good")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Каково состояние льда?\n\n"
             "➢ Хорошее",
    )
    await callback.message.answer(
        text="Спасибо! Желаю Вам продуктивного рабочего дня😊"
    )

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {RUSSIAN_WEEK_DAYS[day_of_week]}')

    start_shift_dict = await state.get_data()

    await send_report(
        message=callback.message,
        state=state,
        data=start_shift_dict,
        date=current_date,
        chat_id=cached_places[start_shift_dict["place"]],
    )
    await callback.answer()


@router_start_shift.callback_query(StateFilter(FSMStartShift.what_state_of_ice), F.data == "bad")
async def process_what_state_of_ice_bad_command(callback: CallbackQuery, state: FSMContext):
    await state.update_data(what_state_of_ice="bad")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Каково состояние льда?\n\n"
             "➢ Плохое",
    )
    await callback.message.answer(
        text="Спасибо! Желаю Вам продуктивного рабочего дня😊"
    )

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(
        f'%d/%m/%Y - {RUSSIAN_WEEK_DAYS[day_of_week]}')

    start_shift_dict = await state.get_data()

    await send_report(
        message=callback.message,
        state=state,
        data=start_shift_dict,
        date=current_date,
        chat_id=cached_places[start_shift_dict["place"]],
    )
    await callback.answer()