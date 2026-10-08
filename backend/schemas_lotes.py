from datetime import date, datetime
from typing import Annotated, Optional

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

NumeroLote = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


class LoteCrear(BaseModel):
    numero_lote: NumeroLote
    fecha_vencimiento: date
    cantidad: int = Field(gt=0)

    # No se carga mercadería que ya venció.
    @field_validator("fecha_vencimiento")
    @classmethod
    def no_vencido(cls, valor: date) -> date:
        if valor < date.today():
            raise ValueError("No se puede cargar un lote ya vencido")
        return valor


class LoteEditar(BaseModel):
    numero_lote: Optional[NumeroLote] = None
    fecha_vencimiento: Optional[date] = None

    # Los datos se pueden corregir, pero no vaciar con null.
    @model_validator(mode="after")
    def sin_nulos(self):
        for campo in ("numero_lote", "fecha_vencimiento"):
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"{campo} no puede ser null")
        return self


class LoteAjuste(BaseModel):
    cantidad: int = Field(ge=0)


class LoteRespuesta(BaseModel):
    id_lote: int
    producto_id: int
    numero_lote: str
    fecha_vencimiento: date
    cantidad: int
    fecha_creacion: datetime
    