from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MedioPago(str, Enum):
    EFECTIVO = "efectivo"
    TARJETA_CREDITO = "tarjeta_credito"
    TARJETA_DEBITO = "tarjeta_debito"
    TRANSFERENCIA = "transferencia"
    QR = "qr"


class LineaVenta(BaseModel):
    producto_id: int
    cantidad: int = Field(gt=0)


class VentaCrear(BaseModel):
    medio_pago: MedioPago
    lineas: list[LineaVenta] = Field(min_length=1)
    # La genera el frontend: si reintenta el mismo pedido, no se duplica la venta.
    clave_operacion: Optional[str] = Field(default=None, min_length=1, max_length=36)


class DetalleRespuesta(BaseModel):
    producto_id: int
    producto: str
    lote_id: int
    cantidad: int
    precio_unitario: float
    subtotal: float


class VentaRespuesta(BaseModel):
    id_venta: int
    numero_comprobante: str
    clave_operacion: Optional[str]
    fecha: datetime
    empleado_id: int
    caja_id: int
    medio_pago: str
    subtotal: float
    monto_cobertura: float
    monto_gravado: float
    monto_exento: float
    total_a_pagar: float
    estado: str
    empleado_anulacion_id: Optional[int]
    fecha_anulacion: Optional[datetime]
    detalles: list[DetalleRespuesta]
