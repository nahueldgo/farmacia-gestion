from decimal import Decimal

import pytest
from pydantic import ValidationError

from schemas_caja import MONTO_MAXIMO, MovimientoCrear, TipoMovimiento


def movimiento(**cambios) -> dict:
    datos = {"tipo": "retiro", "monto": 1500, "motivo": "Devolución de la venta V-00000012"}
    datos.update(cambios)
    return datos


@pytest.mark.parametrize("tipo", ["ingreso", "retiro"])
def test_el_movimiento_es_un_ingreso_o_un_retiro(tipo):
    assert MovimientoCrear(**movimiento(tipo=tipo)).tipo == TipoMovimiento(tipo)


@pytest.mark.parametrize("tipo", ["", "gasto", "Retiro"])
def test_otro_tipo_de_movimiento_se_rechaza(tipo):
    with pytest.raises(ValidationError):
        MovimientoCrear(**movimiento(tipo=tipo))


@pytest.mark.parametrize("monto", [0, -10, "abc"])
def test_el_monto_tiene_que_ser_mayor_a_cero(monto):
    with pytest.raises(ValidationError):
        MovimientoCrear(**movimiento(monto=monto))


def test_el_monto_admite_hasta_dos_decimales():
    assert MovimientoCrear(**movimiento(monto=1500.5)).monto == Decimal("1500.5")
    with pytest.raises(ValidationError):
        MovimientoCrear(**movimiento(monto=10.123))


def test_el_monto_no_puede_pasar_lo_que_entra_en_la_columna():
    assert MovimientoCrear(**movimiento(monto=MONTO_MAXIMO)).monto == MONTO_MAXIMO
    with pytest.raises(ValidationError):
        MovimientoCrear(**movimiento(monto=MONTO_MAXIMO + 1))


def test_el_motivo_se_recorta_y_no_puede_quedar_vacio():
    assert MovimientoCrear(**movimiento(motivo="  Cambio para el mostrador ")).motivo == "Cambio para el mostrador"
    for motivo in ("", "   "):
        with pytest.raises(ValidationError):
            MovimientoCrear(**movimiento(motivo=motivo))


def test_el_motivo_tiene_hasta_200_caracteres():
    assert len(MovimientoCrear(**movimiento(motivo="a" * 200)).motivo) == 200
    with pytest.raises(ValidationError):
        MovimientoCrear(**movimiento(motivo="a" * 201))


@pytest.mark.parametrize("campo", ["tipo", "monto", "motivo"])
def test_todos_los_datos_son_obligatorios(campo):
    datos = movimiento()
    del datos[campo]
    with pytest.raises(ValidationError):
        MovimientoCrear(**datos)
