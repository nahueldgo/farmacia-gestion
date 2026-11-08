from typing import Optional

from pydantic import BaseModel, Field

from schemas_ventas import LineaVenta


class CopagoCalcular(BaseModel):
    obra_social_id: int
    lineas: list[LineaVenta] = Field(min_length=1)


class LineaCopagoRespuesta(BaseModel):
    producto_id: int
    producto: str
    cantidad: int
    precio_unitario: float
    categoria: Optional[str]  # null: el producto no tiene categoría de cobertura
    importe: float
    porcentaje_cobertura: float
    cobertura: float  # lo que paga la obra social
    copago: float  # lo que paga el cliente


class CopagoRespuesta(BaseModel):
    obra_social_id: int
    obra_social: str
    subtotal: float
    monto_cobertura: float
    total_a_pagar: float
    lineas: list[LineaCopagoRespuesta]
