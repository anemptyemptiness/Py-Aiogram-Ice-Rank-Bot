from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from keyboards.adm_keyboard import create_admin_list_kb, create_admin_kb, create_watching_admins_kb
from callbacks.admin import AdminCallbackFactory
from fsm.fsm import FSMAdmin
from .add_employee import router_admin

router_show_admins = Router()
router_admin.include_router(router_show_admins)


@router_show_admins.callback_query(StateFilter(FSMAdmin.in_adm), F.data == "admin_list")
async def process_show_admins_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Список администраторов:",
        reply_markup=create_admin_list_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.watching_admin)


@router_show_admins.callback_query(StateFilter(FSMAdmin.watching_admin), F.data == "go_back")
async def process_go_back_adm_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Добро пожаловать в админскую панель!",
        reply_markup=create_admin_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.in_adm)


@router_show_admins.callback_query(StateFilter(FSMAdmin.watching_admin), AdminCallbackFactory.filter())
async def process_watching_info_command(callback: CallbackQuery, callback_data: AdminCallbackFactory, state: FSMContext):
    await state.update_data(fullname=callback_data.fullname)
    await state.update_data(username=callback_data.username)

    await callback.message.edit_text(
        text="Информация:\n\n"
             f"Имя: {callback_data.fullname}\n"
             f"username: {callback_data.username}",
        reply_markup=create_watching_admins_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.current_admin)


@router_show_admins.callback_query(StateFilter(FSMAdmin.current_admin), F.data == "go_back")
async def process_go_back_from_watching_adm_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Список администраторов:",
        reply_markup=create_admin_list_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.watching_admin)
