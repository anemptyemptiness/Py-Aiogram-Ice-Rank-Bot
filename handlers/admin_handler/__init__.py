from handlers.admin_handler.add_employee import router_admin
from handlers.admin_handler.delete_employee import router_del_emp
from handlers.admin_handler.employee_list import router_show_emp
from handlers.admin_handler.add_admin import router_add_adm
from handlers.admin_handler.delete_admin import router_del_adm
from handlers.admin_handler.admin_list import router_show_admins
from handlers.admin_handler.add_place import router_add_place
from handlers.admin_handler.delete_place import router_del_place
from handlers.admin_handler.place_list import router_show_places

__all__ = [
    "router_admin",
    "router_del_emp",
    "router_show_emp",
    "router_add_adm",
    "router_del_adm",
    "router_show_admins",
    "router_add_place",
    "router_del_place",
    "router_show_places",
]
