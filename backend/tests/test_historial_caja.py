from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

from models import Caja, Empleado
from servicios.base_ventas import RangoDeFechasInvalido
from servicios.caja import ESTADO_ABIERTA, ESTADO_CERRADA, cierres_del_periodo

HOY = date(2026, 11, 11)
AYER = date(2026, 11, 10)
ANTEAYER = date(2026, 11, 9)
LUCIA, MARTIN = 1, 2


def empleado(id_empleado: int, nombre: str, apellido: str) -> Empleado:
    return Empleado(id_empleado=id_empleado, nombre=nombre, apellido=apellido, dni=f"3000000{id_empleado}",
                    rol="auxiliar", fecha_ingreso=date(2026, 1, 1))


def caja(id_caja: int, dia: date, estado: str = ESTADO_CERRADA) -> Caja:
    cerrada = estado == ESTADO_CERRADA
    return Caja(id_caja=id_caja, fecha=dia, empleado_apertura_id=LUCIA, hora_apertura=datetime(dia.year, dia.month, dia.day, 8),
                monto_apertura=Decimal("5000.00"), estado=estado,
                empleado_cierre_id=MARTIN if cerrada else None, hora_cierre=datetime(dia.year, dia.month, dia.day, 20) if cerrada else None,
                monto_cierre_declarado=Decimal("6000.00") if cerrada else None,
                monto_cierre_sistema=Decimal("6100.00") if cerrada else None, diferencia=Decimal("-100.00") if cerrada else None)


# Una caja cerrada hoy, dos ayer (una abierta por Lucía y cerrada por Martín), una anteayer y una todavía abierta.
@pytest.fixture
def session(monkeypatch):
    monkeypatch.setattr("servicios.caja.hoy", lambda: HOY)
    motor = create_engine("sqlite://", poolclass=StaticPool)
    for tabla in (Empleado, Caja):
        tabla.__table__.create(motor)
    with Session(motor) as sesion:
        sesion.add_all([empleado(LUCIA, "Lucía", "Gómez"), empleado(MARTIN, "Martín", "Pérez")])
        sesion.add_all([caja(1, ANTEAYER), caja(2, AYER), caja(3, AYER), caja(4, HOY), caja(5, HOY, ESTADO_ABIERTA)])
        sesion.commit()
        yield sesion


def ids(filas) -> list[int]:
    return [caja.id_caja for caja, _, _ in filas]


def test_sin_fechas_se_listan_los_cierres_de_hoy(session):
    assert ids(cierres_del_periodo(session, None, None)) == [4]


def test_con_una_sola_fecha_se_listan_los_cierres_de_ese_dia(session):
    assert ids(cierres_del_periodo(session, AYER, None)) == [3, 2]
    assert ids(cierres_del_periodo(session, None, AYER)) == [3, 2]


def test_con_las_dos_fechas_se_listan_todos_los_dias_del_rango_del_mas_reciente_al_mas_antiguo(session):
    assert ids(cierres_del_periodo(session, ANTEAYER, HOY)) == [4, 3, 2, 1]


def test_las_cajas_abiertas_no_estan_en_el_historial(session):
    assert 5 not in ids(cierres_del_periodo(session, ANTEAYER, HOY))


def test_un_periodo_sin_cierres_da_una_lista_vacia(session):
    assert cierres_del_periodo(session, date(2026, 10, 1), date(2026, 10, 31)) == []


def test_cada_cierre_trae_quien_abrio_y_quien_cerro(session):
    (_, abrio, cerro), = cierres_del_periodo(session, None, None)
    assert (abrio.nombre, abrio.apellido) == ("Lucía", "Gómez")
    assert (cerro.nombre, cerro.apellido) == ("Martín", "Pérez")


def test_hasta_no_puede_ser_anterior_a_desde(session):
    with pytest.raises(RangoDeFechasInvalido):
        cierres_del_periodo(session, HOY, ANTEAYER)
