from decimal import Decimal

import pytest

from servicios.copago import (
    ESTRATEGIAS,
    EstrategiaCobertura,
    EstrategiaManual,
    LineaACubrir,
    calcular_copago,
    elegir_estrategia,
)

AMBULATORIO, CRONICO, ONCOLOGICO = 1, 2, 4


def d(valor: str) -> Decimal:
    return Decimal(valor)


def reglas_de_prueba() -> dict[int, Decimal]:
    return {AMBULATORIO: d("40"), CRONICO: d("70"), ONCOLOGICO: d("100")}


def manual() -> EstrategiaManual:
    return EstrategiaManual(reglas_de_prueba())


def test_la_obra_social_cubre_el_porcentaje_de_la_categoria():
    resultado = calcular_copago([LineaACubrir(d("1000.00"), AMBULATORIO)], manual())
    linea = resultado.lineas[0]
    assert (linea.porcentaje, linea.cobertura, linea.copago) == (d("40"), d("400.00"), d("600.00"))
    assert (resultado.cobertura, resultado.copago) == (d("400.00"), d("600.00"))


def test_un_producto_sin_categoria_se_paga_completo():
    resultado = calcular_copago([LineaACubrir(d("250.00"), None)], manual())
    assert (resultado.cobertura, resultado.copago) == (d("0"), d("250.00"))


def test_una_categoria_sin_regla_para_esa_obra_social_no_se_cubre():
    resultado = calcular_copago([LineaACubrir(d("250.00"), 3)], manual())
    assert (resultado.lineas[0].porcentaje, resultado.cobertura, resultado.copago) == (d("0"), d("0"), d("250.00"))


def test_al_cien_por_ciento_el_cliente_no_paga():
    resultado = calcular_copago([LineaACubrir(d("1800.50"), ONCOLOGICO)], manual())
    assert (resultado.cobertura, resultado.copago) == (d("1800.50"), d("0.00"))


def test_cada_linea_usa_el_porcentaje_de_su_categoria_y_los_totales_suman_las_lineas():
    lineas = [
        LineaACubrir(d("1000.00"), AMBULATORIO),
        LineaACubrir(d("500.00"), CRONICO),
        LineaACubrir(d("300.00"), None),
    ]
    resultado = calcular_copago(lineas, manual())
    assert [l.cobertura for l in resultado.lineas] == [d("400.00"), d("350.00"), d("0")]
    assert resultado.cobertura == d("750.00")
    assert resultado.copago == d("1050.00")
    assert resultado.cobertura + resultado.copago == d("1800.00")


@pytest.mark.parametrize(
    "importe, porcentaje, cobertura",
    [("33.33", "40", "13.33"), ("10.05", "50", "5.03"), ("10.04", "50", "5.02"), ("100.00", "55.5", "55.50")],
)
def test_la_cobertura_se_redondea_a_dos_decimales_hacia_arriba(importe, porcentaje, cobertura):
    resultado = calcular_copago([LineaACubrir(d(importe), 1)], EstrategiaManual({1: d(porcentaje)}))
    assert resultado.lineas[0].cobertura == d(cobertura)
    assert resultado.lineas[0].cobertura + resultado.lineas[0].copago == d(importe)


# Se redondea línea por línea: así el total es la suma de lo que ve el cliente en el comprobante.
def test_el_total_es_la_suma_de_las_lineas_ya_redondeadas():
    lineas = [LineaACubrir(d("0.05"), 1), LineaACubrir(d("0.05"), 1)]
    resultado = calcular_copago(lineas, EstrategiaManual({1: d("50")}))
    assert [l.cobertura for l in resultado.lineas] == [d("0.03"), d("0.03")]
    assert resultado.cobertura == d("0.06")


def test_sin_lineas_todo_da_cero():
    resultado = calcular_copago([], manual())
    assert (resultado.lineas, resultado.cobertura, resultado.copago) == ([], d("0"), d("0"))


def test_la_estrategia_por_defecto_es_la_manual():
    assert isinstance(elegir_estrategia("manual", reglas_de_prueba()), EstrategiaManual)


# Hasta que exista un validador externo, esas obras sociales se calculan igual con sus reglas cargadas.
@pytest.mark.parametrize("tipo", ["externa", "otra_cosa"])
def test_un_tipo_sin_estrategia_propia_usa_la_manual(tipo):
    estrategia = elegir_estrategia(tipo, reglas_de_prueba())
    assert isinstance(estrategia, EstrategiaManual)
    assert estrategia.porcentaje(LineaACubrir(d("100"), AMBULATORIO)) == d("40")


# Agregar una estrategia nueva no obliga a tocar el cálculo.
def test_se_puede_agregar_una_estrategia_nueva():
    class SiempreMitad(EstrategiaCobertura):
        def __init__(self, reglas):
            pass

        def porcentaje(self, linea):
            return d("50")

    ESTRATEGIAS["mitad"] = SiempreMitad
    try:
        estrategia = elegir_estrategia("mitad", {})
        resultado = calcular_copago([LineaACubrir(d("200.00"), None)], estrategia)
        assert (resultado.cobertura, resultado.copago) == (d("100.00"), d("100.00"))
    finally:
        del ESTRATEGIAS["mitad"]


def test_la_clase_base_no_se_puede_usar_sola():
    with pytest.raises(TypeError):
        EstrategiaCobertura()


@pytest.mark.parametrize("porcentaje", ["-1", "100.01"])
def test_una_estrategia_que_da_un_porcentaje_fuera_de_rango_es_un_error(porcentaje):
    with pytest.raises(ValueError):
        calcular_copago([LineaACubrir(d("100.00"), 1)], EstrategiaManual({1: d(porcentaje)}))
