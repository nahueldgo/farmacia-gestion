from typing import Optional

from pydantic import BaseModel, Field


class ProductoCrear(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    laboratorio_id: Optional[int] = None
    precio: float = Field(gt=0)
    condicion_iva_id: int
    tipo_producto: str
    stock_minimo: int = Field(default=0, ge=0)


class ProductoRespuesta(BaseModel):
    id_producto: int
    nombre: str
    descripcion: Optional[str]
    laboratorio_id: Optional[int]
    precio: float
    condicion_iva_id: int
    tipo_producto: str
    stock_minimo: int
    activo: bool
    stock: int = 0


class ProductoEditar(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    laboratorio_id: Optional[int] = None
    precio: Optional[float] = Field(default=None, gt=0)
    condicion_iva_id: Optional[int] = None
    tipo_producto: Optional[str] = None
    stock_minimo: Optional[int] = Field(default=None, ge=0)
