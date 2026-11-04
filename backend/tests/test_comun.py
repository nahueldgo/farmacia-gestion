import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, select

from comun import guardar_o_409
from models import Cliente


@pytest.fixture
def session():
    motor = create_engine("sqlite://", poolclass=StaticPool)
    Cliente.__table__.create(motor)
    with Session(motor) as sesion:
        yield sesion


def un_cliente(dni: str) -> Cliente:
    return Cliente(nombre="Ana", apellido="Pérez", dni=dni)


def test_guardar_devuelve_el_objeto_ya_guardado(session):
    cliente = guardar_o_409(session, un_cliente("30123456"), "Ya existe")
    assert cliente.id_cliente is not None
    assert session.exec(select(Cliente)).all() == [cliente]


def test_un_dato_unico_repetido_responde_409_con_el_mensaje_dado(session):
    guardar_o_409(session, un_cliente("30123456"), "Ya existe")
    with pytest.raises(HTTPException) as error:
        guardar_o_409(session, un_cliente("30123456"), "Ya existe un cliente con ese DNI")
    assert error.value.status_code == 409
    assert error.value.detail == "Ya existe un cliente con ese DNI"


def test_despues_del_rechazo_la_sesion_sigue_sirviendo(session):
    guardar_o_409(session, un_cliente("30123456"), "Ya existe")
    with pytest.raises(HTTPException):
        guardar_o_409(session, un_cliente("30123456"), "Ya existe")
    guardar_o_409(session, un_cliente("40123456"), "Ya existe")
    assert len(session.exec(select(Cliente)).all()) == 2
