from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select

from comun import empleado_del_usuario, obtener_o_404
from db import get_session
from dependencias import obtener_usuario_actual, requiere_rol
from fechas import a_hora_argentina
from models import DetalleVenta, Empleado, Producto, Venta
from roles import ROLES_OPERATIVOS
from schemas_ventas import DetalleRespuesta, EstadoVenta, VentaCrear, VentaRespuesta, VentaResumen
from servicios.ventas import ErrorDeVenta, crear_venta, ventas_del_periodo

router = APIRouter(prefix="/ventas", tags=["ventas"])

# El dueño no vende: solo consulta.
ROLES_VENDEN = ROLES_OPERATIVOS


def _respuesta(session: Session, venta: Venta) -> VentaRespuesta:
    filas = session.exec(
        select(DetalleVenta, Producto.nombre)
        .where(DetalleVenta.venta_id == venta.id_venta, DetalleVenta.producto_id == Producto.id_producto)
        .order_by(DetalleVenta.id_detalle_venta)
    ).all()
    detalles = [
        DetalleRespuesta(
            producto_id=d.producto_id,
            producto=nombre,
            lote_id=d.lote_id,
            cantidad=d.cantidad,
            precio_unitario=d.precio_unitario,
            subtotal=d.subtotal,
        )
        for d, nombre in filas
    ]
    anulacion = a_hora_argentina(venta.fecha_anulacion) if venta.fecha_anulacion else None
    return VentaRespuesta(
        id_venta=venta.id_venta,
        numero_comprobante=venta.numero_comprobante,
        clave_operacion=venta.clave_operacion,
        fecha=a_hora_argentina(venta.fecha),
        empleado_id=venta.empleado_id,
        caja_id=venta.caja_id,
        medio_pago=venta.medio_pago,
        subtotal=venta.subtotal,
        monto_cobertura=venta.monto_cobertura,
        monto_gravado=venta.monto_gravado,
        monto_exento=venta.monto_exento,
        total_a_pagar=venta.total_a_pagar,
        estado=venta.estado,
        empleado_anulacion_id=venta.empleado_anulacion_id,
        fecha_anulacion=anulacion,
        detalles=detalles,
    )


def _resumen(venta: Venta, empleado: Empleado) -> VentaResumen:
    return VentaResumen(
        id_venta=venta.id_venta,
        numero_comprobante=venta.numero_comprobante,
        fecha=a_hora_argentina(venta.fecha),
        empleado=f"{empleado.nombre} {empleado.apellido}",
        medio_pago=venta.medio_pago,
        total_a_pagar=venta.total_a_pagar,
        estado=venta.estado,
    )


def _como_http(error: ErrorDeVenta) -> HTTPException:
    return HTTPException(status_code=error.estado_http, detail=error.mensaje)


# El empleado sale del token. Si el pedido ya estaba registrado (misma clave_operacion), responde 200 con esa venta.
@router.post("", response_model=VentaRespuesta, status_code=201)
def registrar_venta(
    datos: VentaCrear,
    respuesta: Response,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_VENDEN)),
):
    try:
        venta, creada = crear_venta(session, empleado_del_usuario(session, usuario), datos)
    except ErrorDeVenta as error:
        raise _como_http(error)
    if not creada:
        respuesta.status_code = 200
    return _respuesta(session, venta)


# Por defecto, las ventas de hoy (día de Argentina). Con desde y hasta, todos los días del rango.
@router.get("", response_model=list[VentaResumen])
def listar_ventas(
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    estado: Optional[EstadoVenta] = None,
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    try:
        filas = ventas_del_periodo(session, desde, hasta, estado)
    except ErrorDeVenta as error:
        raise _como_http(error)
    return [_resumen(venta, empleado) for venta, empleado in filas]


@router.get("/{id_venta}", response_model=VentaRespuesta)
def consultar_venta(
    id_venta: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    venta = obtener_o_404(session, Venta, id_venta, "Venta no encontrada")
    return _respuesta(session, venta)
