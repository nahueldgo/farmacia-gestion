from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from schemas_comunes import DatosRecortados

# Lo máximo que entra en la columna monto (NUMERIC(10,2)).
MONTO_MAXIMO = Decimal("99999999.99")


class TipoMovimiento(str, Enum):
    INGRESO = "ingreso"
    RETIRO = "retiro"


class CajaAbrir(BaseModel):
    monto_apertura: float = Field(ge=0)


class CajaCerrar(BaseModel):
    monto_declarado: Decimal = Field(ge=0, le=MONTO_MAXIMO, decimal_places=2)


# Los datos del cierre vienen en None mientras la caja está abierta.
class CajaRespuesta(BaseModel):
    id_caja: int
    fecha: date
    empleado_apertura_id: int
    hora_apertura: datetime
    monto_apertura: float
    estado: str
    empleado_cierre_id: Optional[int] = None
    hora_cierre: Optional[datetime] = None
    monto_cierre_declarado: Optional[float] = None
    monto_cierre_sistema: Optional[float] = None
    diferencia: Optional[float] = None


class MovimientoCrear(DatosRecortados):
    tipo: TipoMovimiento
    monto: Decimal = Field(gt=0, le=MONTO_MAXIMO, decimal_places=2)
    motivo: str = Field(min_length=1, max_length=200)


class MovimientoRespuesta(BaseModel):
    id_movimiento_caja: int
    caja_id: int
    empleado_id: int
    tipo: str
    monto: float
    motivo: str
    hora: datetime


# total_a_pagar es lo que cobró la caja; monto_cobertura, lo que queda a cargo de las obras sociales.
class TotalesRespuesta(BaseModel):
    cantidad: int
    total_a_pagar: float
    monto_cobertura: float


class TotalPorTipoRespuesta(TotalesRespuesta):
    tipo: str


class TotalPorMedioPagoRespuesta(TotalesRespuesta):
    medio_pago: str


class ConsolidadoRespuesta(BaseModel):
    caja: CajaRespuesta
    ventas: TotalesRespuesta
    por_tipo: list[TotalPorTipoRespuesta]
    por_medio_pago: list[TotalPorMedioPagoRespuesta]
    total_ingresos: float
    total_retiros: float
    movimientos: list[MovimientoRespuesta]
    efectivo_esperado: float
