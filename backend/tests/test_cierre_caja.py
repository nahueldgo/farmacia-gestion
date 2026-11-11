from datetime import date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

from models import Caja, MovimientoCaja, Venta
from schemas_caja import MONTO_MAXIMO, CajaCerrar
from servicios.caja import ESTADO_ABIERTA, ESTADO_CERRADA, caja_abierta, cerrar_caja

CAJA, EMPLEADO_CIERRE = 1, 7


def d(valor: str) -> Decimal:
    return Decimal(valor)


def venta(numero: int, medio_pago: str, total: str) -> Venta:
    return Venta(numero_comprobante=f"V-{numero:08d}", empleado_id=1, caja_id=CAJA, medio_pago=medio_pago,
                 subtotal=d(total), monto_cobertura=d("0"), total_a_pagar=d(total), estado="confirmada")


def movimiento(tipo: str, monto: str) -> MovimientoCaja:
    return MovimientoCaja(caja_id=CAJA, empleado_id=1, tipo=tipo, monto=d(monto), motivo="prueba", hora=datetime(2026, 11, 11, 9))


# Caja abierta con 5000 de fondo; en efectivo se cobró 1000, entraron 200 y salieron 100: tendría que haber 6100.
@pytest.fixture
def session():
    motor = create_engine("sqlite://", poolclass=StaticPool)
    for tabla in (Caja, Venta, MovimientoCaja):
        tabla.__table__.create(motor)
    with Session(motor) as sesion:
        sesion.add(Caja(id_caja=CAJA, fecha=date(2026, 11, 11), empleado_apertura_id=1,
                        hora_apertura=datetime(2026, 11, 11, 8), monto_apertura=d("5000.00")))
        sesion.add_all([venta(1, "efectivo", "1000.00"), venta(2, "tarjeta_debito", "800.00"),
                        movimiento("ingreso", "200.00"), movimiento("retiro", "100.00")])
        sesion.commit()
        yield sesion


def cerrar(session, declarado: str) -> Caja:
    caja = caja_abierta(session)
    cerrar_caja(session, caja, EMPLEADO_CIERRE, d(declarado))
    session.commit()
    return session.get(Caja, CAJA)


def test_el_cierre_guarda_quien_cierra_cuando_y_el_estado(session):
    caja = cerrar(session, "6100.00")
    assert caja.estado == ESTADO_CERRADA
    assert caja.empleado_cierre_id == EMPLEADO_CIERRE
    assert caja.hora_cierre is not None


def test_el_cierre_guarda_lo_declarado_y_lo_que_esperaba_el_sistema(session):
    caja = cerrar(session, "6100.00")
    assert (caja.monto_cierre_declarado, caja.monto_cierre_sistema) == (d("6100.00"), d("6100.00"))


def test_lo_cobrado_con_tarjeta_o_transferencia_no_entra_en_el_efectivo_esperado(session):
    assert cerrar(session, "6100.00").monto_cierre_sistema == d("5000.00") + d("1000.00") + d("200.00") - d("100.00")


def test_sin_diferencia_cuando_lo_contado_es_lo_esperado(session):
    assert cerrar(session, "6100.00").diferencia == d("0")


def test_la_diferencia_es_positiva_si_sobra_efectivo(session):
    assert cerrar(session, "6150.50").diferencia == d("50.50")


def test_la_diferencia_es_negativa_si_falta_efectivo(session):
    assert cerrar(session, "6000.00").diferencia == d("-100.00")


def test_el_cierre_devuelve_el_consolidado_de_esa_caja(session):
    consolidado = cerrar_caja(session, caja_abierta(session), EMPLEADO_CIERRE, d("6100.00"))
    assert consolidado.efectivo_esperado == d("6100.00")
    assert (consolidado.ventas.cantidad, consolidado.ventas.total_a_pagar) == (2, d("1800.00"))
    assert (consolidado.total_ingresos, consolidado.total_retiros) == (d("200.00"), d("100.00"))


def test_una_caja_cerrada_ya_no_es_la_caja_abierta(session):
    assert caja_abierta(session).estado == ESTADO_ABIERTA
    cerrar(session, "6100.00")
    assert caja_abierta(session) is None


@pytest.mark.parametrize("monto", [0, "0.00", 6100, "6100.55", MONTO_MAXIMO])
def test_el_monto_declarado_admite_desde_cero_hasta_dos_decimales(monto):
    assert CajaCerrar(monto_declarado=monto).monto_declarado == Decimal(str(monto))


@pytest.mark.parametrize("monto", [-1, "-0.01", "abc", "", None, 10.123, MONTO_MAXIMO + 1])
def test_el_monto_declarado_invalido_se_rechaza(monto):
    with pytest.raises(ValidationError):
        CajaCerrar(monto_declarado=monto)


def test_el_monto_declarado_es_obligatorio():
    with pytest.raises(ValidationError):
        CajaCerrar()
