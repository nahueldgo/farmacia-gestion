import pytest
from pydantic import ValidationError

from schemas_clientes import ClienteCrear


def _cliente(**cambios) -> dict:
    datos = {"nombre": "Ana", "apellido": "Pérez", "dni": "30123456"}
    datos.update(cambios)
    return datos


def test_el_dni_acepta_siete_u_ocho_digitos():
    assert ClienteCrear(**_cliente(dni="5123456")).dni == "5123456"
    assert ClienteCrear(**_cliente(dni="30123456")).dni == "30123456"


@pytest.mark.parametrize("dni", ["", "123456", "123456789", "30.123.456", "3012345a"])
def test_el_dni_con_otro_formato_se_rechaza(dni):
    with pytest.raises(ValidationError):
        ClienteCrear(**_cliente(dni=dni))


def test_los_espacios_de_los_extremos_se_recortan():
    cliente = ClienteCrear(**_cliente(nombre="  Ana ", apellido=" Pérez  ", dni=" 30123456 "))
    assert (cliente.nombre, cliente.apellido, cliente.dni) == ("Ana", "Pérez", "30123456")


@pytest.mark.parametrize("campo", ["nombre", "apellido"])
def test_el_nombre_y_el_apellido_no_pueden_quedar_vacios(campo):
    with pytest.raises(ValidationError):
        ClienteCrear(**_cliente(**{campo: "   "}))


def test_el_telefono_es_opcional_y_en_blanco_vale_como_ausente():
    assert ClienteCrear(**_cliente()).telefono is None
    assert ClienteCrear(**_cliente(telefono="   ")).telefono is None
    assert ClienteCrear(**_cliente(telefono=" 3364 123456 ")).telefono == "3364 123456"
