from enum import Enum


class Rol(str, Enum):
    AUXILIAR = "auxiliar"
    FARMACEUTICO = "farmaceutico"
    DUENO = "dueno"


# Grupos de roles que usan varios routers: un solo lugar para cambiar quién puede qué.
SOLO_DUENO = (Rol.DUENO,)
SOLO_FARMACEUTICO = (Rol.FARMACEUTICO,)
ROLES_OPERATIVOS = (Rol.FARMACEUTICO, Rol.AUXILIAR)
TODOS_LOS_ROLES = (Rol.FARMACEUTICO, Rol.AUXILIAR, Rol.DUENO)
