from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import aliased
from sqlmodel import Session, select

from fechas import ahora_utc, hoy
from models import Caja, Empleado, MovimientoCaja, Venta
from schemas_caja import TipoMovimiento
from schemas_ventas import EstadoVenta, MedioPago
from servicios.base_ventas import resolver_periodo

CERO = Decimal("0")
MOSTRADOR = "mostrador"
CON_COBERTURA = "con_cobertura"
ESTADO_ABIERTA = "abierta"
ESTADO_CERRADA = "cerrada"


def _abierta():
    return select(Caja).where(Caja.estado == ESTADO_ABIERTA)


def caja_abierta(session: Session) -> Optional[Caja]:
    return session.exec(_abierta()).first()


# Las ventas y los movimientos toman una marca sobre la fila de la caja y el cierre la bloquea entera: el cierre espera
# a lo que está en curso y lo cuenta, y lo que llega después encuentra la caja ya cerrada.
def caja_abierta_para_operar(session: Session) -> Optional[Caja]:
    return session.exec(_abierta().with_for_update(key_share=True)).first()


def caja_abierta_para_cerrar(session: Session) -> Optional[Caja]:
    return session.exec(_abierta().with_for_update()).first()


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


# Arqueo: lo contado contra lo que el sistema dice que tendría que haber en efectivo. Una diferencia positiva es un
# sobrante y una negativa, un faltante. No hace commit: lo hace quien llama.
def cerrar_caja(session: Session, caja: Caja, id_empleado: int, monto_declarado: Decimal) -> Consolidado:
    consolidado = consolidar_caja(session, caja)
    caja.empleado_cierre_id = id_empleado
    caja.hora_cierre = ahora_utc()
    caja.monto_cierre_declarado = monto_declarado
    caja.monto_cierre_sistema = consolidado.efectivo_esperado
    caja.diferencia = monto_declarado - consolidado.efectivo_esperado
    caja.estado = ESTADO_CERRADA
    session.add(caja)
    return consolidado


# Las cajas cerradas de un período, de la más reciente a la más antigua, con quién la abrió y quién la cerró.
# El día de una caja es el de su apertura. Sin fechas, las de hoy; con una sola, ese día; con las dos, todo el rango.
def cierres_del_periodo(
    session: Session, desde: Optional[date], hasta: Optional[date]
) -> list[tuple[Caja, Empleado, Empleado]]:
    primer_dia, ultimo_dia = resolver_periodo(desde, hasta, hoy())
    abrio, cerro = aliased(Empleado), aliased(Empleado)
    consulta = (
        select(Caja, abrio, cerro)
        .join(abrio, Caja.empleado_apertura_id == abrio.id_empleado)
        .join(cerro, Caja.empleado_cierre_id == cerro.id_empleado)
        .where(Caja.estado == ESTADO_CERRADA, Caja.fecha >= primer_dia, Caja.fecha <= ultimo_dia)
        .order_by(Caja.fecha.desc(), Caja.id_caja.desc())
    )
    return session.exec(consulta).all()
