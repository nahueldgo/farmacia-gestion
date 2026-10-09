from datetime import date

from pydantic import BaseModel


class AlertaStockBajo(BaseModel):
    id_producto: int
    nombre: str
    stock: int
    stock_minimo: int
    faltante: int


class AlertaVencimiento(BaseModel):
    id_lote: int
    producto_id: int
    producto: str
    numero_lote: str
    fecha_vencimiento: date
    cantidad: int
    dias_restantes: int
    estado: str
    