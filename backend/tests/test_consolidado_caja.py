from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

from models import Caja, MovimientoCaja, Venta
from servicios.caja import CON_COBERTURA, MOSTRADOR, consolidar_caja

CAJA, OTRA_CAJA = 1, 2
OBRA_SOCIAL = 3


def d(valor: str) -> Decimal:
    return Decimal(valor)


def venta(numero: int, medio_pago: str, total: str, *, cobertura: str = "0", caja: int = CAJA, estado: str = "confirmada"):
    return Venta(
        numero_comprobante=f"V-{numero:08d}",
        empleado_id=1,
        caja_id=caja,
        medio_pago=medio_pago,
        obra_social_id=OBRA_SOCIAL if d(cobertura) > 0 else None,
        subtotal=d(total) + d(cobertura),
        monto_cobertura=d(cobertura),
        total_a_pagar=d(total),
        estado=estado,
    )


def movimiento(tipo: str, monto: str, *, caja: int = CAJA, hora: int = 9) -> MovimientoCaja:
    return MovimientoCaja(caja_id=caja, empleado_id=1, tipo=tipo, monto=d(monto), motivo="prueba", hora=datetime(2026, 11, 10, hora))


@pytest.fixture
def session():
    motor = create_engine("sqlite://", poolclass=StaticPool)
    for tabla in (Caja, Venta, MovimientoCaja):
        tabla.__table__.create(motor)
    with Session(motor) as sesion:
        for id_caja in (CAJA, OTRA_CAJA):
            sesion.add(Caja(id_caja=id_caja, fecha=date(2026, 11, 10), empleado_apertura_id=1,
                            hora_apertura=datetime(2026, 11, 10, 8), monto_apertura=d("5000.00")))
        sesion.commit()
        yield sesion


def consolidar(session, id_caja: int = CAJA):
    return consolidar_caja(session, session.get(Caja, id_caja))


def test_una_caja_sin_movimientos_tiene_todo_en_cero_y_solo_el_fondo_inicial(session):
    consolidado = consolidar(session)
    assert (consolidado.ventas.cantidad, consolidado.ventas.total_a_pagar) == (0, d("0"))
    assert consolidado.movimientos == []
    assert (consolidado.total_ingresos, consolidado.total_retiros) == (d("0"), d("0"))
    assert consolidado.efectivo_esperado == d("5000.00")


def test_el_consolidado_siempre_trae_todos_los_tipos_y_medios_de_pago_en_orden(session):
    consolidado = consolidar(session)
    assert list(consolidado.por_tipo) == [MOSTRADOR, CON_COBERTURA]
    assert list(consolidado.por_medio_pago) == ["efectivo", "tarjeta_credito", "tarjeta_debito", "transferencia", "qr"]


def test_las_ventas_se_suman_por_medio_de_pago(session):
    session.add_all([
        venta(1, "efectivo", "1000.00"), venta(2, "efectivo", "250.50"),
        venta(3, "tarjeta_debito", "700.00"), venta(4, "qr", "300.00"),
    ])
    session.commit()
    medios = consolidar(session).por_medio_pago
    assert (medios["efectivo"].cantidad, medios["efectivo"].total_a_pagar) == (2, d("1250.50"))
    assert (medios["tarjeta_debito"].cantidad, medios["tarjeta_debito"].total_a_pagar) == (1, d("700.00"))
    assert (medios["qr"].cantidad, medios["qr"].total_a_pagar) == (1, d("300.00"))
    assert (medios["tarjeta_credito"].cantidad, medios["transferencia"].cantidad) == (0, 0)


def test_las_ventas_con_obra_social_se_cuentan_aparte_de_las_de_mostrador(session):
    session.add_all([
        venta(1, "efectivo", "1000.00"),
        venta(2, "efectivo", "600.00", cobertura="400.00"),
        venta(3, "tarjeta_credito", "300.00", cobertura="700.00"),
    ])
    session.commit()
    tipos = consolidar(session).por_tipo
    assert (tipos[MOSTRADOR].cantidad, tipos[MOSTRADOR].total_a_pagar, tipos[MOSTRADOR].monto_cobertura) == (1, d("1000.00"), d("0"))
    assert (tipos[CON_COBERTURA].cantidad, tipos[CON_COBERTURA].total_a_pagar, tipos[CON_COBERTURA].monto_cobertura) == (
        2, d("900.00"), d("1100.00"))


def test_el_total_de_ventas_es_lo_que_cobro_la_caja_y_lo_que_cubren_las_obras_sociales(session):
    session.add_all([venta(1, "efectivo", "1000.00"), venta(2, "qr", "600.00", cobertura="400.00")])
    session.commit()
    ventas = consolidar(session).ventas
    assert (ventas.cantidad, ventas.total_a_pagar, ventas.monto_cobertura) == (2, d("1600.00"), d("400.00"))


def test_las_ventas_anuladas_no_se_cuentan(session):
    session.add_all([venta(1, "efectivo", "1000.00"), venta(2, "efectivo", "900.00", estado="anulada")])
    session.commit()
    consolidado = consolidar(session)
    assert (consolidado.ventas.cantidad, consolidado.ventas.total_a_pagar) == (1, d("1000.00"))
    assert consolidado.efectivo_esperado == d("6000.00")


def test_solo_cuentan_las_ventas_y_los_movimientos_de_esa_caja(session):
    session.add_all([
        venta(1, "efectivo", "1000.00"), venta(2, "efectivo", "9999.00", caja=OTRA_CAJA),
        movimiento("ingreso", "200.00"), movimiento("retiro", "5000.00", caja=OTRA_CAJA),
    ])
    session.commit()
    consolidado = consolidar(session)
    assert consolidado.ventas.total_a_pagar == d("1000.00")
    assert (consolidado.total_ingresos, consolidado.total_retiros) == (d("200.00"), d("0"))
    assert len(consolidado.movimientos) == 1


def test_el_efectivo_esperado_suma_el_fondo_las_ventas_en_efectivo_y_los_ingresos_y_resta_los_retiros(session):
    session.add_all([
        venta(1, "efectivo", "1000.00"), venta(2, "efectivo", "500.00", cobertura="500.00"),
        venta(3, "tarjeta_credito", "800.00"), venta(4, "transferencia", "200.00"),
        movimiento("ingreso", "300.00"), movimiento("ingreso", "50.00"), movimiento("retiro", "1200.00"),
    ])
    session.commit()
    consolidado = consolidar(session)
    assert (consolidado.total_ingresos, consolidado.total_retiros) == (d("350.00"), d("1200.00"))
    # 5000 de fondo + 1500 cobrados en efectivo + 350 de ingresos - 1200 de retiros; lo cobrado con tarjeta o transferencia no está en la caja.
    assert consolidado.efectivo_esperado == d("5650.00")


def test_los_movimientos_salen_en_el_orden_en_que_se_hicieron(session):
    session.add_all([movimiento("retiro", "10.00", hora=12), movimiento("ingreso", "20.00", hora=9), movimiento("retiro", "30.00", hora=10)])
    session.commit()
    assert [m.monto for m in consolidar(session).movimientos] == [d("20.00"), d("30.00"), d("10.00")]
