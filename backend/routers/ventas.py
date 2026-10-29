from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select

from comun import empleado_del_usuario
from db import get_session
from dependencias import requiere_rol
from fechas import a_hora_argentina
from models import DetalleVenta, Producto, Venta
from roles import ROLES_OPERATIVOS
from schemas_ventas import DetalleRespuesta, VentaCrear, VentaRespuesta
from servicios.ventas import ErrorDeVenta, crear_venta

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
        raise HTTPException(status_code=error.estado_http, detail=error.mensaje)
    if not creada:
        respuesta.status_code = 200
    return _respuesta(session, venta)
