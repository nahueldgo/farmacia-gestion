import pytest
from pydantic import ValidationError

from schemas_auth import LoginRequest, LoginResponse


@pytest.mark.parametrize("campo", ["nombre_usuario", "nombreUsuario"])
def test_el_login_acepta_el_nombre_de_usuario_con_las_dos_versiones(campo):
    datos = LoginRequest(**{campo: "maria", "contrasena": "clave1234"})
    assert datos.nombre_usuario == "maria"


def test_el_login_sigue_exigiendo_el_nombre_de_usuario():
    with pytest.raises(ValidationError):
        LoginRequest(contrasena="clave1234")


@pytest.mark.parametrize("pendiente", [True, False])
def test_la_respuesta_trae_las_dos_versiones_del_cambio_de_contrasena(pendiente):
    respuesta = LoginResponse(token="t", nombre="Maria", rol="auxiliar", debe_cambiar_contrasena=pendiente)
    datos = respuesta.model_dump()
    assert datos["debe_cambiar_contrasena"] is pendiente
    assert datos["debeCambiarContrasena"] is pendiente


def test_el_cambio_de_contrasena_pendiente_es_falso_por_defecto():
    datos = LoginResponse(token="t", nombre="Maria", rol="auxiliar").model_dump()
    assert (datos["debe_cambiar_contrasena"], datos["debeCambiarContrasena"]) == (False, False)
