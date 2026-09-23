from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel

class Empleado(SQLModel, table=True):
    __tablename__ = "empleado"

    id_empleado: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    apellido: str
    dni: str
    rol: str
    matricula_profesional: Optional[str] = None
    fecha_ingreso: date
    activo: bool = True

class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"

    id_usuario: Optional[int] = Field(default=None, primary_key=True)
    empleado_id: int = Field(foreign_key="empleado.id_empleado", unique=True)
    nombre_usuario: str = Field(unique=True)
    email: str = Field(unique=True)
    contrasena_hash: str
    activo: bool = True
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    ultimo_login: Optional[datetime] = None