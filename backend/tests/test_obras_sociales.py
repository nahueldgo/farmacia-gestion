import pytest
from pydantic import ValidationError

from schemas_obras_sociales import ObraSocialCrear, ObraSocialEditar, TipoValidacion


def test_solo_el_nombre_es_obligatorio_y_la_validacion_es_manual_por_defecto():
    obra_social = ObraSocialCrear(nombre="IOMA")
    assert obra_social.cuit is None
    assert obra_social.contacto is None
    assert obra_social.tipo_validacion == TipoValidacion.MANUAL


@pytest.mark.parametrize("cuit", ["3012345678", "301234567890", "30-12345678-9", "3012345678a"])
def test_el_cuit_con_otro_formato_se_rechaza(cuit):
    with pytest.raises(ValidationError):
        ObraSocialCrear(nombre="IOMA", cuit=cuit)


def test_el_cuit_acepta_once_digitos():
    assert ObraSocialCrear(nombre="IOMA", cuit="30123456789").cuit == "30123456789"


def test_los_espacios_se_recortan_y_el_cuit_y_el_contacto_en_blanco_valen_como_ausentes():
    obra_social = ObraSocialCrear(nombre="  IOMA ", cuit="   ", contacto="  ")
    assert obra_social.nombre == "IOMA"
    assert obra_social.cuit is None
    assert obra_social.contacto is None


def test_el_nombre_no_puede_quedar_vacio():
    with pytest.raises(ValidationError):
        ObraSocialCrear(nombre="   ")


def test_el_tipo_de_validacion_solo_acepta_manual_o_externa():
    assert ObraSocialCrear(nombre="IOMA", tipo_validacion="externa").tipo_validacion == TipoValidacion.EXTERNA
    with pytest.raises(ValidationError):
        ObraSocialCrear(nombre="IOMA", tipo_validacion="automatica")


def test_al_editar_solo_figura_lo_que_se_mando():
    assert ObraSocialEditar(contacto="3364 000000").model_dump(exclude_unset=True) == {"contacto": "3364 000000"}


def test_al_editar_el_cuit_se_puede_vaciar_con_null_y_se_distingue_de_no_mandarlo():
    assert ObraSocialEditar(cuit=None).model_dump(exclude_unset=True) == {"cuit": None}
    assert ObraSocialEditar().model_dump(exclude_unset=True) == {}
