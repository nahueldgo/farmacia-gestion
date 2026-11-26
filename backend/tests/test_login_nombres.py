import pytest
from pydantic import ValidationError

from schemas_auth import LoginRequest, LoginResponse


def test_el_login_recibe_el_nombre_de_usuario():
    datos = LoginRequest(nombre_usuario="maria", contrasena="clave1234")
    assert datos.nombre_usuario == "maria"


@pytest.mark.parametrize("extra", [{}, {"nombreUsuario": "maria"}])
def test_el_login_exige_el_nombre_de_usuario_con_guion_bajo(extra):
    with pytest.raises(ValidationError):
        LoginRequest(contrasena="clave1234", **extra)


@pytest.mark.parametrize("pendiente", [True, False])
def test_la_respuesta_informa_el_cambio_de_contrasena_con_un_solo_nombre(pendiente):
    respuesta = LoginResponse(token="t", nombre="Maria", rol="auxiliar", debe_cambiar_contrasena=pendiente)
    assert respuesta.model_dump() == {
        "token": "t",
        "nombre": "Maria",
        "rol": "auxiliar",
        "debe_cambiar_contrasena": pendiente,
    }


def test_el_cambio_de_contrasena_pendiente_es_falso_por_defecto():
    respuesta = LoginResponse(token="t", nombre="Maria", rol="auxiliar")
    assert respuesta.debe_cambiar_contrasena is False
