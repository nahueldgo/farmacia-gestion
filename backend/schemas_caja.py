from datetime import date, datetime

from pydantic import BaseModel, Field


class CajaAbrir(BaseModel):
    monto_apertura: float = Field(ge=0)


class CajaRespuesta(BaseModel):
    id_caja: int
    fecha: date
    empleado_apertura_id: int
    hora_apertura: datetime
    monto_apertura: float
    estado: str
