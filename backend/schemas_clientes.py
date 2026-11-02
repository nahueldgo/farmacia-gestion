from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# DNI argentino: solo dígitos, sin puntos ni espacios (7 u 8 números).
PATRON_DNI = r"^\d{7,8}$"


class ClienteCrear(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    dni: str = Field(pattern=PATRON_DNI)
    telefono: Optional[str] = Field(default=None, max_length=30)

    # Un teléfono en blanco es lo mismo que no mandarlo.
    @field_validator("telefono")
    @classmethod
    def telefono_vacio_es_nada(cls, telefono: Optional[str]) -> Optional[str]:
        return telefono or None


class ClienteRespuesta(BaseModel):
    id_cliente: int
    nombre: str
    apellido: str
    dni: str
    telefono: Optional[str]
