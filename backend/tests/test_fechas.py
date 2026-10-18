from datetime import date, datetime, timedelta

from fechas import a_hora_argentina, ahora, ahora_utc, hoy, rango_utc_del_dia


# Argentina va 3 h atrás de UTC y no tiene horario de verano.
def test_ahora_esta_en_hora_argentina():
    assert ahora().utcoffset() == timedelta(hours=-3)


def test_hoy_es_el_dia_de_argentina():
    assert hoy() == ahora().date()


def test_ahora_utc_no_lleva_zona_y_va_3_horas_adelante():
    guardada = ahora_utc()
    assert guardada.tzinfo is None
    diferencia = guardada - ahora().replace(tzinfo=None)
    assert abs(diferencia - timedelta(hours=3)) < timedelta(seconds=5)


def test_a_hora_argentina_resta_3_horas():
    # 01:30 UTC del 19/10 son las 22:30 del 18/10 en Argentina
    assert a_hora_argentina(datetime(2026, 10, 19, 1, 30)).replace(tzinfo=None) == datetime(2026, 10, 18, 22, 30)


def test_rango_del_dia_argentino_en_utc():
    inicio, fin = rango_utc_del_dia(date(2026, 10, 18))
    assert inicio == datetime(2026, 10, 18, 3, 0)
    assert fin == datetime(2026, 10, 19, 3, 0)


# El error que queremos evitar: una venta a las 22:30 de Argentina se guarda como 01:30 UTC del día siguiente.
def test_una_venta_de_las_22_30_cae_en_el_dia_de_argentina():
    venta_guardada = datetime(2026, 10, 19, 1, 30)
    inicio, fin = rango_utc_del_dia(date(2026, 10, 18))
    assert inicio <= venta_guardada < fin
    inicio_siguiente, fin_siguiente = rango_utc_del_dia(date(2026, 10, 19))
    assert not (inicio_siguiente <= venta_guardada < fin_siguiente)


def test_los_rangos_de_dias_consecutivos_no_se_superponen():
    _, fin = rango_utc_del_dia(date(2026, 10, 18))
    inicio_siguiente, _ = rango_utc_del_dia(date(2026, 10, 19))
    assert fin == inicio_siguiente
