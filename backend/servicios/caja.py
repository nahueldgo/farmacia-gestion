from dataclasses import dataclass
from decimal import Decimal

from sqlmodel import Session, select

from models import Caja, MovimientoCaja, Venta
from schemas_caja import TipoMovimiento
from schemas_ventas import EstadoVenta, MedioPago

CERO = Decimal("0")
MOSTRADOR = "mostrador"
CON_COBERTURA = "con_cobertura"


@dataclass
class Totales:
    cantidad: int = 0
    total_a_pagar: Decimal = CERO
    monto_cobertura: Decimal = CERO

    def sumar(self, venta: Venta) -> None:
        self.cantidad += 1
        self.total_a_pagar += venta.total_a_pagar
        self.monto_cobertura += venta.monto_cobertura


@dataclass
class Consolidado:
    ventas: Totales
    por_tipo: dict[str, Totales]
    por_medio_pago: dict[str, Totales]
    movimientos: list[MovimientoCaja]
    total_ingresos: Decimal
    total_retiros: Decimal
    efectivo_esperado: Decimal


def _total_de_movimientos(movimientos: list[MovimientoCaja], tipo: TipoMovimiento) -> Decimal:
    return sum((m.monto for m in movimientos if m.tipo == tipo.value), CERO)


# Lo de una caja: las ventas confirmadas (las anuladas no cuentan) por tipo y por medio de pago, los movimientos
# manuales y el efectivo que tendría que haber. Los ingresos y retiros manuales son siempre en efectivo.
def consolidar_caja(session: Session, caja: Caja) -> Consolidado:
    ventas = session.exec(
        select(Venta).where(Venta.caja_id == caja.id_caja, Venta.estado == EstadoVenta.CONFIRMADA.value)
    ).all()
    movimientos = session.exec(
        select(MovimientoCaja)
        .where(MovimientoCaja.caja_id == caja.id_caja)
        .order_by(MovimientoCaja.hora, MovimientoCaja.id_movimiento_caja)
    ).all()

    total = Totales()
    por_tipo = {MOSTRADOR: Totales(), CON_COBERTURA: Totales()}
    por_medio_pago = {medio.value: Totales() for medio in MedioPago}
    for venta in ventas:
        total.sumar(venta)
        por_tipo[MOSTRADOR if venta.obra_social_id is None else CON_COBERTURA].sumar(venta)
        por_medio_pago[venta.medio_pago].sumar(venta)

    ingresos = _total_de_movimientos(movimientos, TipoMovimiento.INGRESO)
    retiros = _total_de_movimientos(movimientos, TipoMovimiento.RETIRO)
    efectivo_esperado = caja.monto_apertura + por_medio_pago[MedioPago.EFECTIVO.value].total_a_pagar + ingresos - retiros
    return Consolidado(total, por_tipo, por_medio_pago, movimientos, ingresos, retiros, efectivo_esperado)
