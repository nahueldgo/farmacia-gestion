from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

from models import CategoriaCoberturaObraSocial, ObraSocial, ReglaCobertura
from schemas_reglas_cobertura import ReglaCoberturaGuardar


@pytest.mark.parametrize("porcentaje", [0, 40, 70.5, "100", "12.25"])
def test_el_porcentaje_acepta_de_0_a_100(porcentaje):
    assert ReglaCoberturaGuardar(porcentaje_cobertura=porcentaje).porcentaje_cobertura == Decimal(str(porcentaje))


@pytest.mark.parametrize("porcentaje", [-1, -0.01, 100.01, 101, 12.345, "abc", None, "NaN"])
def test_el_porcentaje_fuera_de_rango_o_con_mas_de_dos_decimales_se_rechaza(porcentaje):
    with pytest.raises(ValidationError):
        ReglaCoberturaGuardar(porcentaje_cobertura=porcentaje)


def test_el_porcentaje_es_obligatorio():
    with pytest.raises(ValidationError):
        ReglaCoberturaGuardar()


@pytest.fixture
def session():
    motor = create_engine("sqlite://", poolclass=StaticPool)
    for tabla in (ObraSocial, CategoriaCoberturaObraSocial, ReglaCobertura):
        tabla.__table__.create(motor)
    with Session(motor) as sesion:
        sesion.add(ObraSocial(nombre="IOMA"))
        sesion.add(CategoriaCoberturaObraSocial(nombre="ambulatorio"))
        sesion.commit()
        yield sesion


# La base garantiza una sola regla por obra social y categoría, también ante dos pedidos simultáneos.
def test_no_puede_haber_dos_reglas_para_la_misma_obra_social_y_categoria(session):
    session.add(ReglaCobertura(obra_social_id=1, categoria_cobertura_obra_social_id=1, porcentaje_cobertura=40))
    session.commit()
    session.add(ReglaCobertura(obra_social_id=1, categoria_cobertura_obra_social_id=1, porcentaje_cobertura=70))
    with pytest.raises(IntegrityError):
        session.commit()
