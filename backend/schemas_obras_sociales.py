from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from schemas_comunes import DatosRecortados, en_blanco_es_nada

# CUIT: solo los 11 dígitos, sin guiones.
PATRON_CUIT = r"^\d{11}$"


class TipoValidacion(str, Enum):
    MANUAL = "manual"
    EXTERNA = "externa"


class ObraSocialCrear(DatosRecortados):
    nombre: str = Field(min_length=1, max_length=100)
    cuit: Optional[str] = Field(default=None, pattern=PATRON_CUIT)
    contacto: Optional[str] = Field(default=None, max_length=100)
    tipo_validacion: TipoValidacion = TipoValidacion.MANUAL

    _limpiar = field_validator("cuit", "contacto", mode="before")(en_blanco_es_nada)


class ObraSocialEditar(DatosRecortados):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    cuit: Optional[str] = Field(default=None, pattern=PATRON_CUIT)
    contacto: Optional[str] = Field(default=None, max_length=100)
    tipo_validacion: Optional[TipoValidacion] = None

    _limpiar = field_validator("cuit", "contacto", mode="before")(en_blanco_es_nada)


class ObraSocialRespuesta(BaseModel):
    id_obra_social: int
    nombre: str
    cuit: Optional[str]
    contacto: Optional[str]
    tipo_validacion: str
    activo: bool
