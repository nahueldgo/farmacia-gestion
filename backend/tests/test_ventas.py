from datetime import date
from decimal import Decimal

import pytest

from schemas_ventas import LineaVenta
from servicios.ventas import (
    RangoDeFechasInvalido,
    calcular_montos,
    formatear_comprobante,
    importe,
    juntar_lineas,
    resolver_periodo,
)

HOY = date(2026, 10, 29)


def test_el_comprobante_lleva_prefijo_y_ocho_digitos():
    assert formatear_comprobante(1) == "V-00000001"
    assert formatear_comprobante(123) == "V-00000123"


def test_el_importe_se_redondea_a_dos_decimales():
    assert importe(Decimal("33.335"), 3) == Decimal("100.01")
    assert importe(Decimal("10.00"), 4) == Decimal("40.00")


def test_un_producto_repetido_se_junta_en_una_sola_linea():
    lineas = [LineaVenta(producto_id=7, cantidad=2), LineaVenta(producto_id=3, cantidad=1), LineaVenta(producto_id=7, cantidad=3)]
    assert juntar_lineas(lineas) == {3: 1, 7: 5}


# Siempre se procesan en el mismo orden: así dos ventas simultáneas no se bloquean entre sí.
def test_las_lineas_se_ordenan_por_producto():
    lineas = [LineaVenta(producto_id=9, cantidad=1), LineaVenta(producto_id=2, cantidad=1)]
    assert list(juntar_lineas(lineas)) == [2, 9]


def test_los_montos_separan_gravado_y_exento():
    # 2 x $100 con IVA 21% y 1 x $50,50 exento
    montos = calcular_montos([(Decimal("100.00"), Decimal("21"), 2), (Decimal("50.50"), Decimal("0"), 1)])
    assert montos.subtotal == Decimal("250.50")
    assert montos.gravado == Decimal("200.00")
    assert montos.exento == Decimal("50.50")
    assert montos.total == Decimal("250.50")


def test_una_venta_solo_de_medicamentos_no_tiene_gravado():
    montos = calcular_montos([(Decimal("1200.00"), Decimal("0"), 3)])
    assert montos.gravado == Decimal("0")
    assert montos.exento == Decimal("3600.00")


def test_el_iva_reducido_tambien_cuenta_como_gravado():
    montos = calcular_montos([(Decimal("110.00"), Decimal("10.5"), 1)])
    assert montos.gravado == Decimal("110.00")
    assert montos.exento == Decimal("0")


def test_gravado_mas_exento_siempre_da_el_subtotal():
    montos = calcular_montos([(Decimal("33.33"), Decimal("21"), 3), (Decimal("10.10"), Decimal("0"), 7)])
    assert montos.gravado + montos.exento == montos.subtotal == montos.total


def test_sin_fechas_se_listan_las_ventas_de_hoy():
    assert resolver_periodo(None, None, HOY) == (HOY, HOY)


def test_con_una_sola_fecha_se_lista_ese_dia():
    assert resolver_periodo(date(2026, 10, 20), None, HOY) == (date(2026, 10, 20), date(2026, 10, 20))
    assert resolver_periodo(None, date(2026, 10, 20), HOY) == (date(2026, 10, 20), date(2026, 10, 20))


def test_con_las_dos_fechas_se_lista_el_rango():
    assert resolver_periodo(date(2026, 10, 1), date(2026, 10, 15), HOY) == (date(2026, 10, 1), date(2026, 10, 15))


def test_un_rango_de_un_solo_dia_es_valido():
    assert resolver_periodo(HOY, HOY, HOY) == (HOY, HOY)


def test_hasta_no_puede_ser_anterior_a_desde():
    with pytest.raises(RangoDeFechasInvalido):
        resolver_periodo(date(2026, 10, 15), date(2026, 10, 1), HOY)
