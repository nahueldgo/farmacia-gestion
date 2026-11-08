from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from db import get_session
from dependencias import requiere_rol
from roles import ROLES_OPERATIVOS
from schemas_copago import CopagoCalcular, CopagoRespuesta, LineaCopagoRespuesta
from servicios.copago_venta import CopagoDeVenta, calcular_copago_de_venta
from servicios.ventas import ErrorDeVenta

router = APIRouter(prefix="/copago", tags=["copago"])

# Lo usa quien registra la venta; el dueño no vende.
ROLES_CALCULAN = ROLES_OPERATIVOS


def _respuesta(copago: CopagoDeVenta) -> CopagoRespuesta:
    lineas = [
        LineaCopagoRespuesta(
            producto_id=c.producto.id_producto,
            producto=c.producto.nombre,
            cantidad=c.cantidad,
            precio_unitario=c.producto.precio,
            categoria=c.categoria,
            importe=c.importe,
            porcentaje_cobertura=c.cubierta.porcentaje,
            cobertura=c.cubierta.cobertura,
            copago=c.cubierta.copago,
        )
        for c in copago.lineas
    ]
    return CopagoRespuesta(
        obra_social_id=copago.obra_social.id_obra_social,
        obra_social=copago.obra_social.nombre,
        subtotal=copago.subtotal,
        monto_cobertura=copago.cobertura,
        total_a_pagar=copago.total_a_pagar,
        lineas=lineas,
    )


# Calcula la cobertura y el total a cobrar sin registrar la venta: no guarda nada ni toca el stock.
@router.post("/calcular", response_model=CopagoRespuesta)
def calcular(
    datos: CopagoCalcular,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_CALCULAN)),
):
    try:
        copago = calcular_copago_de_venta(session, datos.obra_social_id, datos.lineas)
    except ErrorDeVenta as error:
        raise HTTPException(status_code=error.estado_http, detail=error.mensaje)
    return _respuesta(copago)
