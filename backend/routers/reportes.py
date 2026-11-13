from dataclasses import asdict
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from db import get_session
from dependencias import requiere_rol
from roles import SOLO_DUENO
from schemas_reportes import ProductoDelReporte, ReporteVentasPorProducto
from servicios.base_ventas import RangoDeFechasInvalido
from servicios.reportes import ventas_por_producto

router = APIRouter(prefix="/reportes", tags=["reportes"])


# Solo el dueño ve los reportes: los otros roles reciben 403.
# Por defecto, las ventas de hoy (día de Argentina). Con desde y hasta, todos los días del rango.
@router.get("/ventas-por-producto", response_model=ReporteVentasPorProducto)
def reporte_ventas_por_producto(
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*SOLO_DUENO)),
):
    try:
        reporte = ventas_por_producto(session, desde, hasta)
    except RangoDeFechasInvalido as error:
        raise HTTPException(status_code=error.estado_http, detail=error.mensaje)
    return ReporteVentasPorProducto(
        desde=reporte.desde,
        hasta=reporte.hasta,
        cantidad_tickets=reporte.cantidad_tickets,
        total_facturado=reporte.total_facturado,
        productos=[ProductoDelReporte(**asdict(fila)) for fila in reporte.productos],
    )
