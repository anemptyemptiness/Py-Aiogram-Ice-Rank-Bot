from aiogram.types import CallbackQuery
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from keyboards.adm_keyboard import create_employee_list_kb, create_admin_kb, create_delete_kb
from callbacks.employee import EmployeeCallbackFactory
from fsm.fsm import FSMAdmin
from .add_employee import router_admin
from db import DB

router_del_emp = Router()
router_admin.include_routers(router_del_emp)


@router_del_emp.callback_query(StateFilter(FSMAdmin.in_adm), F.data == "delete_employee")
async def process_del_emp_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Список сотрудников:",
        reply_markup=create_employee_list_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.which_employee_to_delete)


@router_del_emp.callback_query(StateFilter(FSMAdmin.which_employee_to_delete), EmployeeCallbackFactory.filter())
async def process_which_emp_to_del_command(callback: CallbackQuery, callback_data: EmployeeCallbackFactory, state: FSMContext):
    await state.update_data(fullname=callback_data.fullname)
    await state.update_data(username=callback_data.username)

    await callback.message.edit_text(
        text="Информация:\n\n"
             f"Имя: {callback_data.fullname}\n"
             f"username: {callback_data.username}",
        reply_markup=create_delete_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.deleting_employee)


@router_del_emp.callback_query(StateFilter(FSMAdmin.which_employee_to_delete), F.data == "go_back")
async def process_go_back_which_do_delete_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Добро пожаловать в админскую панель!",
        reply_markup=create_admin_kb(),
    )
    await state.set_state(FSMAdmin.in_adm)


@router_del_emp.callback_query(StateFilter(FSMAdmin.deleting_employee), F.data == "delete")
async def process_deleting_employee_command(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    DB.delete_employee(
        fullname=data["fullname"],
        username=data["username"],
    )

    await callback.message.edit_text(
        text=f"Сотрудник {data['fullname']} успешно удален!\n\n"
             "Список сотрудников:",
        reply_markup=create_employee_list_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.which_employee_to_delete)


@router_del_emp.callback_query(StateFilter(FSMAdmin.deleting_employee), F.data == "go_back")
async def process_go_back_del_emp_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Список сотрудников:",
        reply_markup=create_employee_list_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.which_employee_to_delete)