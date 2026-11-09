import pytest
from pydantic import ValidationError

from schemas_ventas import VentaCrear

LINEAS = [{"producto_id": 5, "cantidad": 2}]


def pedido(**cambios) -> dict:
    datos = {"medio_pago": "efectivo", "lineas": LINEAS}
    datos.update(cambios)
    return datos


def test_la_venta_de_mostrador_no_lleva_obra_social_ni_cliente_ni_receta():
    venta = VentaCrear(**pedido())
    assert (venta.obra_social_id, venta.cliente_id, venta.receta_verificada) == (None, None, False)


def test_la_venta_con_obra_social_lleva_cliente_y_receta_verificada():
    venta = VentaCrear(**pedido(obra_social_id=3, cliente_id=7, receta_verificada=True))
    assert (venta.obra_social_id, venta.cliente_id, venta.receta_verificada) == (3, 7, True)


def test_con_obra_social_el_cliente_es_obligatorio():
    with pytest.raises(ValidationError, match="necesita un cliente"):
        VentaCrear(**pedido(obra_social_id=3, receta_verificada=True))


@pytest.mark.parametrize("receta", [False, None])
def test_con_obra_social_la_receta_tiene_que_estar_verificada(receta):
    cambios = {} if receta is None else {"receta_verificada": receta}
    with pytest.raises(ValidationError, match="receta verificada"):
        VentaCrear(**pedido(obra_social_id=3, cliente_id=7, **cambios))


@pytest.mark.parametrize("cambios", [{"cliente_id": 7}, {"receta_verificada": True}])
def test_sin_obra_social_no_se_aceptan_cliente_ni_receta(cambios):
    with pytest.raises(ValidationError, match="solo se indican en una venta con obra social"):
        VentaCrear(**pedido(**cambios))
