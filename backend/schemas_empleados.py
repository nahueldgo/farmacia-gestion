from datetime import date
from typing import Optional

from pydantic import BaseModel

from roles import Rol


class EmpleadoCrear(BaseModel):
    nombre: str
    apellido: str
    dni: str
    rol: Rol
    matricula_profesional: Optional[str] = None
    fecha_ingreso: date
    nombre_usuario: str
    email: str
    contrasena: str


class EmpleadoRespuesta(BaseModel):
    id_empleado: int
    nombre: str
    apellido: str
    dni: str
    rol: str
    matricula_profesional: Optional[str] = None
    fecha_ingreso: date
    activo: bool
    nombre_usuario: str
    email: str


class CambiarContrasena(BaseModel):
    contrasena_nueva: str

    