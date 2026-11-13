from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

from models import DetalleVenta, Producto, Venta
from servicios.base_ventas import RangoDeFechasInvalido
from servicios.reportes import ventas_por_producto

HOY = date(2026, 11, 12)
CREMA, GEL = 1, 2


def d(valor: str) -> Decimal:
    return Decimal(valor)


# Las horas se escriben en UTC, como se guardan en la base: Argentina va 3 horas atrás.
def venta(id_venta: int, fecha: datetime, estado: str = "confirmada", total: str = "0") -> Venta:
    return Venta(id_venta=id_venta, numero_comprobante=f"V-{id_venta:08d}", empleado_id=1, caja_id=1, medio_pago="efectivo",
                 subtotal=d(total), monto_cobertura=d("0"), total_a_pagar=d(total), estado=estado, fecha=fecha)


def renglon(id_venta: int, id_producto: int, cantidad: int, precio: str) -> DetalleVenta:
    return DetalleVenta(venta_id=id_venta, producto_id=id_producto, lote_id=1, cantidad=cantidad,
                        precio_unitario=d(precio), subtotal=d(precio) * cantidad)


@pytest.fixture
def session(monkeypatch):
    monkeypatch.setattr("servicios.reportes.hoy", lambda: HOY)
    motor = create_engine("sqlite://", poolclass=StaticPool)
    for tabla in (Producto, Venta, DetalleVenta):
        tabla.__table__.create(motor)
    with Session(motor) as sesion:
        sesion.add_all([
            Producto(id_producto=CREMA, nombre="Crema", precio=d("300.00"), condicion_iva_id=1, tipo_producto="perfumeria"),
            Producto(id_producto=GEL, nombre="Gel", precio=d("1000.00"), condicion_iva_id=1, tipo_producto="perfumeria"),
        ])
        sesion.commit()
        yield sesion


def cargar(session, *objetos):
    session.add_all(objetos)
    session.commit()


MEDIODIA = datetime(2026, 11, 12, 15)  # 12:00 en Argentina


def test_cada_producto_trae_sus_tickets_unidades_importe_y_porcentaje(session):
    cargar(session, venta(1, MEDIODIA), venta(2, MEDIODIA),
           renglon(1, GEL, 1, "1000.00"), renglon(1, CREMA, 2, "300.00"), renglon(2, CREMA, 1, "300.00"))
    reporte = ventas_por_producto(session, None, None)
    gel, crema = reporte.productos
    assert (gel.producto, gel.tickets, gel.unidades, gel.importe, gel.porcentaje_facturacion) == ("Gel", 1, 1, d("1000.00"), d("52.63"))
    assert (crema.producto, crema.tickets, crema.unidades, crema.importe, crema.porcentaje_facturacion) == ("Crema", 2, 3, d("900.00"), d("47.37"))
    assert (reporte.total_facturado, reporte.cantidad_tickets) == (d("1900.00"), 2)


def test_un_producto_de_dos_lotes_en_la_misma_venta_cuenta_un_solo_ticket(session):
    cargar(session, venta(1, MEDIODIA), renglon(1, GEL, 2, "1000.00"), renglon(1, GEL, 3, "1000.00"))
    (gel,) = ventas_por_producto(session, None, None).productos
    assert (gel.tickets, gel.unidades, gel.importe) == (1, 5, d("5000.00"))


def test_las_ventas_anuladas_no_cuentan(session):
    cargar(session, venta(1, MEDIODIA), venta(2, MEDIODIA, estado="anulada"),
           renglon(1, GEL, 1, "1000.00"), renglon(2, GEL, 4, "1000.00"), renglon(2, CREMA, 1, "300.00"))
    reporte = ventas_por_producto(session, None, None)
    assert [(p.producto, p.tickets, p.unidades) for p in reporte.productos] == [("Gel", 1, 1)]
    assert (reporte.total_facturado, reporte.cantidad_tickets) == (d("1000.00"), 1)


def test_el_importe_sale_del_detalle_y_no_del_precio_actual_del_producto(session):
    cargar(session, venta(1, MEDIODIA), renglon(1, GEL, 1, "800.00"))
    assert ventas_por_producto(session, None, None).productos[0].importe == d("800.00")


def test_una_venta_con_cobertura_factura_el_precio_de_lista(session):
    cargar(session, venta(1, MEDIODIA, total="600.00"), renglon(1, GEL, 1, "1000.00"))
    assert ventas_por_producto(session, None, None).total_facturado == d("1000.00")


def test_va_del_producto_que_mas_facturo_al_que_menos_y_a_igual_importe_por_nombre(session):
    cargar(session, venta(1, MEDIODIA), renglon(1, GEL, 1, "300.00"), renglon(1, CREMA, 1, "300.00"))
    assert [p.producto for p in ventas_por_producto(session, None, None).productos] == ["Crema", "Gel"]
    cargar(session, venta(2, MEDIODIA), renglon(2, GEL, 5, "300.00"))
    assert [p.producto for p in ventas_por_producto(session, None, None).productos] == ["Gel", "Crema"]


def test_los_porcentajes_se_redondean_a_dos_decimales(session):
    cargar(session, venta(1, MEDIODIA), renglon(1, GEL, 1, "100.00"), renglon(1, CREMA, 2, "100.00"))
    gel, crema = sorted(ventas_por_producto(session, None, None).productos, key=lambda p: p.importe)
    assert (gel.porcentaje_facturacion, crema.porcentaje_facturacion) == (d("33.33"), d("66.67"))


def test_sin_ventas_en_el_periodo_todo_da_cero(session):
    reporte = ventas_por_producto(session, None, None)
    assert (reporte.productos, reporte.total_facturado, reporte.cantidad_tickets) == ([], d("0"), 0)


def test_sin_fechas_es_hoy_con_una_sola_es_ese_dia_y_con_las_dos_todo_el_rango(session):
    cargar(session, venta(1, datetime(2026, 11, 12, 15)), venta(2, datetime(2026, 11, 10, 15)), venta(3, datetime(2026, 11, 1, 15)),
           renglon(1, GEL, 1, "100.00"), renglon(2, GEL, 1, "100.00"), renglon(3, GEL, 1, "100.00"))
    assert ventas_por_producto(session, None, None).cantidad_tickets == 1
    assert ventas_por_producto(session, date(2026, 11, 10), None).cantidad_tickets == 1
    reporte = ventas_por_producto(session, date(2026, 11, 1), date(2026, 11, 12))
    assert (reporte.desde, reporte.hasta, reporte.cantidad_tickets) == (date(2026, 11, 1), date(2026, 11, 12), 3)


def test_hasta_no_puede_ser_anterior_a_desde(session):
    with pytest.raises(RangoDeFechasInvalido):
        ventas_por_producto(session, date(2026, 11, 12), date(2026, 11, 1))


# 22:30 del 10/11 en Argentina son las 01:30 del 11/11 en UTC: la venta es del 10 y no del 11.
def test_una_venta_de_las_22_30_de_argentina_cuenta_en_su_dia_y_no_en_el_siguiente(session):
    cargar(session, venta(1, datetime(2026, 11, 11, 1, 30)), renglon(1, GEL, 1, "100.00"))
    assert ventas_por_producto(session, date(2026, 11, 10), date(2026, 11, 10)).cantidad_tickets == 1
    assert ventas_por_producto(session, date(2026, 11, 11), date(2026, 11, 11)).cantidad_tickets == 0


# Las 00:30 del 11/11 en Argentina son las 03:30 del 11/11 en UTC: ya es del 11 y no del 10.
def test_una_venta_de_las_00_30_de_argentina_cuenta_en_el_dia_nuevo(session):
    cargar(session, venta(1, datetime(2026, 11, 11, 3, 30)), renglon(1, GEL, 1, "100.00"))
    assert ventas_por_producto(session, date(2026, 11, 10), date(2026, 11, 10)).cantidad_tickets == 0
    assert ventas_por_producto(session, date(2026, 11, 11), date(2026, 11, 11)).cantidad_tickets == 1


# El 30/11 a las 23:30 en Argentina ya es el 1/12 en UTC (02:30), pero la venta es de noviembre.
def test_en_el_cambio_de_mes_la_venta_de_las_23_30_del_ultimo_dia_es_del_mes_que_termina(session):
    cargar(session, venta(1, datetime(2026, 12, 1, 2, 30)), venta(2, datetime(2026, 12, 1, 3, 30)),
           renglon(1, GEL, 1, "100.00"), renglon(2, GEL, 1, "100.00"))
    noviembre = ventas_por_producto(session, date(2026, 11, 1), date(2026, 11, 30))
    diciembre = ventas_por_producto(session, date(2026, 12, 1), date(2026, 12, 31))
    assert (noviembre.cantidad_tickets, diciembre.cantidad_tickets) == (1, 1)
