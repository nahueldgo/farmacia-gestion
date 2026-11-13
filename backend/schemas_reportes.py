from datetime import date

from pydantic import BaseModel


# tickets es en cuántas ventas apareció el producto; importe, lo que facturó, al precio final de lista tal como se vendió
# (con el IVA en los productos gravados y sin IVA en los exentos); porcentaje_facturacion, qué parte de lo facturado en
# el período es suya.
class ProductoDelReporte(BaseModel):
    producto_id: int
    producto: str
    tickets: int
    unidades: int
    importe: float
    porcentaje_facturacion: float


# cantidad_tickets son todas las ventas confirmadas del período; total_facturado, la suma de los importes de los productos.
class ReporteVentasPorProducto(BaseModel):
    desde: date
    hasta: date
    cantidad_tickets: int
    total_facturado: float
    productos: list[ProductoDelReporte]
