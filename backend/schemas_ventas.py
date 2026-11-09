from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class MedioPago(str, Enum):
    EFECTIVO = "efectivo"
    TARJETA_CREDITO = "tarjeta_credito"
    TARJETA_DEBITO = "tarjeta_debito"
    TRANSFERENCIA = "transferencia"
    QR = "qr"


class EstadoVenta(str, Enum):
    CONFIRMADA = "confirmada"
    ANULADA = "anulada"


class LineaVenta(BaseModel):
    producto_id: int
    cantidad: int = Field(gt=0)


class VentaCrear(BaseModel):
    medio_pago: MedioPago
    lineas: list[LineaVenta] = Field(min_length=1)
    # La genera el frontend: si reintenta el mismo pedido, no se duplica la venta.
    clave_operacion: Optional[str] = Field(default=None, min_length=1, max_length=36)
    # Solo en la venta con cobertura: la obra social, el afiliado y la confirmación de que se controló la receta.
    obra_social_id: Optional[int] = None
    cliente_id: Optional[int] = None
    receta_verificada: bool = False

    @model_validator(mode="after")
    def _cobertura_coherente(self):
        if self.obra_social_id is None:
            if self.cliente_id is not None or self.receta_verificada:
                raise ValueError("El cliente y la receta solo se indican en una venta con obra social")
        elif self.cliente_id is None:
            raise ValueError("Una venta con obra social necesita un cliente")
        elif not self.receta_verificada:
            raise ValueError("Una venta con obra social necesita la receta verificada")
        return self


class DetalleRespuesta(BaseModel):
    producto_id: int
    producto: str
    lote_id: int
    cantidad: int
    precio_unitario: float
    subtotal: float


class VentaResumen(BaseModel):
    id_venta: int
    numero_comprobante: str
    fecha: datetime
    empleado: str
    medio_pago: str
    total_a_pagar: float
    estado: str


class VentaRespuesta(BaseModel):
    id_venta: int
    numero_comprobante: str
    clave_operacion: Optional[str]
    fecha: datetime
    empleado_id: int
    caja_id: int
    obra_social_id: Optional[int]
    cliente_id: Optional[int]
    receta_verificada: bool
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
