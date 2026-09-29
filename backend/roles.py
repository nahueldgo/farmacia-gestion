from enum import Enum


class Rol(str, Enum):
    AUXILIAR = "auxiliar"
    FARMACEUTICO = "farmaceutico"
    DUENO = "dueno"
    