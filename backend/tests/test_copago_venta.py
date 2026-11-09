from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

from models import CategoriaCoberturaObraSocial, Medicamento, ObraSocial, Producto, ReglaCobertura
from schemas_ventas import LineaVenta
from servicios.base_ventas import ProductoDadoDeBaja, ProductoNoEncontrado
from servicios.copago_venta import ObraSocialDadaDeBaja, ObraSocialNoEncontrada, calcular_copago_de_venta

IOMA, OSDE, EXTERNA, DE_BAJA = 1, 2, 3, 4
AMBULATORIO, CRONICO = 1, 2
ANALGESICO, CREMA, CRONICO_X, RETIRADO = 1, 2, 3, 4


def d(valor: str) -> Decimal:
    return Decimal(valor)


def pedido(*partes: tuple[int, int]) -> list[LineaVenta]:
    return [LineaVenta(producto_id=p, cantidad=c) for p, c in partes]


@pytest.fixture
def session():
    motor = create_engine("sqlite://", poolclass=StaticPool)
    for tabla in (Producto, Medicamento, CategoriaCoberturaObraSocial, ObraSocial, ReglaCobertura):
        tabla.__table__.create(motor)
    with Session(motor) as sesion:
        sesion.add_all([
            CategoriaCoberturaObraSocial(nombre="ambulatorio"),
            CategoriaCoberturaObraSocial(nombre="cronico"),
            ObraSocial(nombre="IOMA"),
            ObraSocial(nombre="OSDE"),
            ObraSocial(nombre="Externa", tipo_validacion="externa"),
            ObraSocial(nombre="Vieja", activo=False),
        ])
        for id_producto, nombre, precio, tipo, activo in [
            (ANALGESICO, "Analgésico", "1000.00", "medicamento", True),
            (CREMA, "Crema", "300.00", "perfumeria", True),
            (CRONICO_X, "Pastilla crónica", "500.00", "medicamento", True),
            (RETIRADO, "Retirado", "100.00", "medicamento", False),
        ]:
            sesion.add(Producto(id_producto=id_producto, nombre=nombre, precio=d(precio), condicion_iva_id=1,
                                tipo_producto=tipo, activo=activo))
        sesion.add(Medicamento(producto_id=ANALGESICO, principio_activo_id=1, concentracion="500 mg",
                               forma_farmaceutica_id=1, categoria_cobertura_obra_social_id=AMBULATORIO))
        sesion.add(Medicamento(producto_id=CRONICO_X, principio_activo_id=1, concentracion="10 mg",
                               forma_farmaceutica_id=1, categoria_cobertura_obra_social_id=CRONICO))
        sesion.add(Medicamento(producto_id=RETIRADO, principio_activo_id=1, concentracion="1 mg",
                               forma_farmaceutica_id=1))
        # IOMA cubre ambulatorio al 40% y crónico al 70%; OSDE solo ambulatorio al 100%, y su regla de crónico está inactiva.
        for obra_social, categoria, porcentaje, activa in [
            (IOMA, AMBULATORIO, "40", True), (IOMA, CRONICO, "70", True),
            (OSDE, AMBULATORIO, "100", True), (OSDE, CRONICO, "90", False),
            (EXTERNA, AMBULATORIO, "50", True),
        ]:
            sesion.add(ReglaCobertura(obra_social_id=obra_social, categoria_cobertura_obra_social_id=categoria,
                                      porcentaje_cobertura=d(porcentaje), activo=activa))
        sesion.commit()
        yield sesion


def test_cada_producto_usa_la_cobertura_de_su_categoria(session):
    copago = calcular_copago_de_venta(session, IOMA, pedido((ANALGESICO, 2), (CRONICO_X, 1), (CREMA, 1)))
    # Las líneas salen ordenadas por producto, no por el orden del pedido.
    analgesico, crema, cronico = copago.lineas
    assert (analgesico.importe, analgesico.cubierta.porcentaje, analgesico.cubierta.cobertura) == (d("2000.00"), d("40"), d("800.00"))
    assert (cronico.importe, cronico.cubierta.porcentaje, cronico.cubierta.cobertura) == (d("500.00"), d("70"), d("350.00"))
    assert analgesico.categoria == "ambulatorio" and cronico.categoria == "cronico"
    assert (crema.categoria, crema.cubierta.porcentaje, crema.cubierta.cobertura) == (None, d("0"), d("0"))


def test_los_totales_cierran(session):
    copago = calcular_copago_de_venta(session, IOMA, pedido((ANALGESICO, 2), (CRONICO_X, 1), (CREMA, 1)))
    assert copago.subtotal == d("2800.00")
    assert copago.cobertura == d("1150.00")
    assert copago.total_a_pagar == d("1650.00")
    assert copago.cobertura + copago.total_a_pagar == copago.subtotal
    assert copago.obra_social.nombre == "IOMA"


def test_un_producto_repetido_se_suma_en_una_sola_linea(session):
    copago = calcular_copago_de_venta(session, IOMA, pedido((ANALGESICO, 1), (CREMA, 1), (ANALGESICO, 2)))
    assert [(l.producto.id_producto, l.cantidad) for l in copago.lineas] == [(ANALGESICO, 3), (CREMA, 1)]
    assert copago.lineas[0].importe == d("3000.00")


def test_una_categoria_sin_regla_para_esa_obra_social_se_paga_completa(session):
    copago = calcular_copago_de_venta(session, OSDE, pedido((CRONICO_X, 1)))
    assert (copago.cobertura, copago.total_a_pagar) == (d("0"), d("500.00"))


def test_una_regla_inactiva_no_cuenta(session):
    copago = calcular_copago_de_venta(session, OSDE, pedido((ANALGESICO, 1), (CRONICO_X, 1)))
    assert [l.cubierta.porcentaje for l in copago.lineas] == [d("100"), d("0")]
    assert copago.total_a_pagar == d("500.00")


def test_al_cien_por_ciento_el_cliente_no_paga(session):
    copago = calcular_copago_de_venta(session, OSDE, pedido((ANALGESICO, 1)))
    assert (copago.cobertura, copago.total_a_pagar) == (d("1000.00"), d("0.00"))


def test_una_obra_social_de_validacion_externa_se_calcula_con_sus_reglas(session):
    copago = calcular_copago_de_venta(session, EXTERNA, pedido((ANALGESICO, 1)))
    assert copago.cobertura == d("500.00")


def test_una_obra_social_que_no_existe_se_rechaza(session):
    with pytest.raises(ObraSocialNoEncontrada) as error:
        calcular_copago_de_venta(session, 999, pedido((ANALGESICO, 1)))
    assert (error.value.estado_http, error.value.mensaje) == (404, "Obra social no encontrada")


def test_una_obra_social_dada_de_baja_se_rechaza(session):
    with pytest.raises(ObraSocialDadaDeBaja) as error:
        calcular_copago_de_venta(session, DE_BAJA, pedido((ANALGESICO, 1)))
    assert error.value.estado_http == 409


def test_un_producto_que_no_existe_o_esta_dado_de_baja_se_rechaza_como_en_la_venta(session):
    with pytest.raises(ProductoNoEncontrado):
        calcular_copago_de_venta(session, IOMA, pedido((999, 1)))
    with pytest.raises(ProductoDadoDeBaja):
        calcular_copago_de_venta(session, IOMA, pedido((RETIRADO, 1)))


def test_calcular_no_guarda_nada(session):
    calcular_copago_de_venta(session, IOMA, pedido((ANALGESICO, 2)))
    assert not session.new and not session.dirty
