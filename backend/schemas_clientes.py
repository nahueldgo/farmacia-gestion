from typing import Optional

from pydantic import BaseModel, Field, field_validator

from schemas_comunes import DatosRecortados, en_blanco_es_nada

# DNI argentino: solo dígitos, sin puntos ni espacios (7 u 8 números).
PATRON_DNI = r"^\d{7,8}$"


class ClienteCrear(DatosRecortados):
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    dni: str = Field(pattern=PATRON_DNI)
    telefono: Optional[str] = Field(default=None, max_length=30)

    _limpiar = field_validator("telefono", mode="before")(en_blanco_es_nada)


class ClienteRespuesta(BaseModel):
    id_cliente: int
    nombre: str
    apellido: str
    dni: str
    telefono: Optional[str]
