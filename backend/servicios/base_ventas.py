from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from sqlmodel import Session

from models import Producto
from schemas_ventas import LineaVenta

DOS_DECIMALES = Decimal("0.01")


# Lo que comparten el registro de la venta, el cálculo del copago y los listados por período (ventas y cierres de caja).
# Errores de negocio: el router los convierte en la respuesta HTTP que indica cada uno.
class ErrorDeVenta(Exception):
    estado_http = 422

    def __init__(self, mensaje: str):
        self.mensaje = mensaje
        super().__init__(mensaje)


class RangoDeFechasInvalido(ErrorDeVenta):
    estado_http = 422


class ProductoNoEncontrado(ErrorDeVenta):
    estado_http = 404


class ProductoDadoDeBaja(ErrorDeVenta):
    estado_http = 409


# Los importes se redondean a centavos, hacia arriba en la mitad (0,005 pasa a 0,01).
def a_centavos(monto: Decimal) -> Decimal:
    return monto.quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)


def importe(precio: Decimal, cantidad: int) -> Decimal:
    return a_centavos(precio * cantidad)


# Sin fechas, las de hoy. Con una sola, ese día. Con las dos, todos los días entre ellas.
def resolver_periodo(desde: Optional[date], hasta: Optional[date], dia_actual: date) -> tuple[date, date]:
    primer_dia = desde or hasta or dia_actual
    ultimo_dia = hasta or primer_dia
    if ultimo_dia < primer_dia:
        raise RangoDeFechasInvalido("La fecha hasta no puede ser anterior a la fecha desde")
    return primer_dia, ultimo_dia


# Si un producto viene en dos líneas, se suman: así se descuenta y se bloquea una sola vez.
def juntar_lineas(lineas: list[LineaVenta]) -> dict[int, int]:
    juntas: dict[int, int] = {}
    for linea in lineas:
        juntas[linea.producto_id] = juntas.get(linea.producto_id, 0) + linea.cantidad
    # Siempre en el mismo orden, para que dos ventas simultáneas no se bloqueen entre sí.
    return dict(sorted(juntas.items()))


# El producto tiene que existir y no estar dado de baja.
def producto_vendible(session: Session, id_producto: int) -> Producto:
    producto = session.get(Producto, id_producto)
    if producto is None:
        raise ProductoNoEncontrado(f"No existe el producto {id_producto}")
    if not producto.activo:
        raise ProductoDadoDeBaja(f"El producto {producto.nombre} está dado de baja")
    return producto
