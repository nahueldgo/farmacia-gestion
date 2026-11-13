from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlmodel import Session, select

from fechas import hoy, rango_utc_del_dia
from models import DetalleVenta, Producto, Venta
from schemas_ventas import EstadoVenta
from servicios.base_ventas import a_centavos, resolver_periodo

CERO = Decimal("0")
CIEN = Decimal("100")


@dataclass
class FilaDeProducto:
    producto_id: int
    producto: str
    tickets: int  # en cuántas ventas apareció el producto
    unidades: int
    importe: Decimal
    porcentaje_facturacion: Decimal


@dataclass
class VentasPorProducto:
    desde: date
    hasta: date
    cantidad_tickets: int  # las ventas del período, con o sin ese producto
    total_facturado: Decimal
    productos: list[FilaDeProducto]


def _porcentaje(parte: Decimal, total: Decimal) -> Decimal:
    return a_centavos(parte * CIEN / total) if total else CERO


# Las ventas confirmadas del período (las anuladas no cuentan), con los días cortados en hora de Argentina.
def _confirmadas_entre(primer_dia: date, ultimo_dia: date) -> tuple:
    inicio, _ = rango_utc_del_dia(primer_dia)
    _, fin = rango_utc_del_dia(ultimo_dia)
    return Venta.estado == EstadoVenta.CONFIRMADA.value, Venta.fecha >= inicio, Venta.fecha < fin


# Por producto: en cuántas ventas apareció, cuántas unidades se vendieron y cuánto facturó. Los importes salen del
# detalle de cada venta (el precio final de ese momento, con el IVA que lleve cada producto y sin descontar la cobertura),
# no del precio actual.
# Va del que más facturó al que menos. Sin fechas, hoy; con una sola, ese día; con las dos, todos los días del rango.
def ventas_por_producto(session: Session, desde: Optional[date], hasta: Optional[date]) -> VentasPorProducto:
    primer_dia, ultimo_dia = resolver_periodo(desde, hasta, hoy())
    confirmadas = _confirmadas_entre(primer_dia, ultimo_dia)

    renglones = session.exec(
        select(DetalleVenta, Producto.nombre)
        .join(Venta, Venta.id_venta == DetalleVenta.venta_id)
        .join(Producto, Producto.id_producto == DetalleVenta.producto_id)
        .where(*confirmadas)
    ).all()
    ventas = session.exec(select(Venta.id_venta).where(*confirmadas)).all()

    filas: dict[int, FilaDeProducto] = {}
    ventas_de_cada_producto: dict[int, set[int]] = {}
    for detalle, nombre in renglones:
        fila = filas.setdefault(detalle.producto_id, FilaDeProducto(detalle.producto_id, nombre, 0, 0, CERO, CERO))
        ventas_de_cada_producto.setdefault(detalle.producto_id, set()).add(detalle.venta_id)
        fila.unidades += detalle.cantidad
        fila.importe += detalle.subtotal

    total = sum((fila.importe for fila in filas.values()), CERO)
    for id_producto, fila in filas.items():
        fila.tickets = len(ventas_de_cada_producto[id_producto])
        fila.porcentaje_facturacion = _porcentaje(fila.importe, total)

    productos = sorted(filas.values(), key=lambda fila: (-fila.importe, fila.producto))
    return VentasPorProducto(primer_dia, ultimo_dia, len(ventas), total, productos)
