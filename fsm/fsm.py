from aiogram.fsm.state import StatesGroup, State


class FSMStartShift(StatesGroup):
    place = State()
    employee_photo = State()
    working_place_photo = State()
    cloakroom_photo = State()
    ice_rank_is_dry = State()
    is_defects = State()
    defects_photo = State()
    laces = State()
    hats_and_socks = State()
    is_penguins = State()
    penguins_defects_photo = State()
    is_boxes = State()
    boxes_defects_photo = State()
    is_defend = State()
    is_music = State()
    is_alert = State()


class FSMDailyChecking(StatesGroup):
    place = State()
    check_people_pays = State()
    working_place_photo = State()
    is_ice_rank_defects = State()
    defects_photo = State()
    book_of_suggestions = State()
    book_info = State()
    is_strong_defects = State()
    count_tickets = State()
    summary = State()


class FSMFinishShift(StatesGroup):
    place = State()
    is_disinfection = State()
    ice_rank_on_drying = State()
    is_ice_rank_defects = State()
    defects_photo = State()
    is_hats_and_socks = State()
    is_depend_defects = State()
    depend_defects_photo = State()
    is_music = State()
    is_alert_off = State()
    is_working_place_closed = State()


class FSMEncashment(StatesGroup):
    place = State()
    cash = State()
    online_cash = State()
    qr_code = State()
    summary = State()
    receipts_photo = State()
    is_benefits = State()
    benefits_photo = State()


class FSMAdmin(StatesGroup):
    # главное меню
    rules = State()
    in_adm = State()

    # добавление сотрудника в БД
    add_employee_id = State()
    add_employee_name = State()
    add_employee_username = State()
    add_employee_phone = State()
    check_employee = State()
    rename_employee = State()
    reid_employee = State()
    reusername_employee = State()

    # удаление сотрудника из БД
    which_employee_to_delete = State()
    deleting_employee = State()

    # получить список сотрудников
    watching_employees = State()
    current_employee = State()

    # добавить админа в БД
    add_admin_id = State()
    add_admin_name = State()
    add_admin_username = State()
    add_admin_phone = State()
    check_admin = State()
    rename_admin = State()
    reid_admin = State()
    reusername_admin = State()

    # удалить админа в БД
    which_admin_to_delete = State()
    deleting_admin = State()

    # получить список админов
    watching_admin = State()
    current_admin = State()

    # добавить рабочую точку в БД
    add_place = State()
    add_place_id = State()
    check_place = State()
    rename_place = State()
    reid_place = State()

    # удалить рабочую точку в БД
    which_place_to_delete = State()
    deleting_place = State()

    # получить список рабочих точек
    watching_place = State()
    current_place = State()
