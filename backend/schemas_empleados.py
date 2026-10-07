from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator

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
    contrasena: str = Field(min_length=8)

    # Un farmacéutico necesita matrícula profesional.
    @model_validator(mode="after")
    def matricula_si_es_farmaceutico(self):
        if self.rol == Rol.FARMACEUTICO and not (self.matricula_profesional or "").strip():
            raise ValueError("El farmacéutico debe tener matrícula profesional")
        return self


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
    contrasena_nueva: str = Field(min_length=8)


class EmpleadoEditar(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1)
    apellido: Optional[str] = Field(default=None, min_length=1)
    rol: Optional[Rol] = None
    matricula_profesional: Optional[str] = None
    fecha_ingreso: Optional[date] = None
    email: Optional[str] = Field(default=None, min_length=1)

    # Los datos obligatorios se pueden cambiar, pero no vaciar con null.
    @model_validator(mode="after")
    def sin_nulos(self):
        for campo in ("nombre", "apellido", "rol", "fecha_ingreso", "email"):
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"{campo} no puede ser null")
        return self
