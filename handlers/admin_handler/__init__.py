from handlers.admin_handler.add_employee import router_admin
from handlers.admin_handler.delete_employee import router_del_emp
from handlers.admin_handler.employee_list import router_show_emp
from handlers.admin_handler.add_admin import router_add_adm

__all__ = [
    "router_admin",
    "router_del_emp",
    "router_show_emp",
    "router_add_adm",
]
