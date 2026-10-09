from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case
from sqlmodel import Session, func, select

from db import get_session
from dependencias import requiere_rol
from fechas import hoy
from models import Lote, Producto
from roles import Rol
from schemas_alertas import AlertaStockBajo, AlertaVencimiento

router = APIRouter(prefix="/alertas", tags=["alertas"])

ROLES_ALERTAS = (Rol.FARMACEUTICO,)


# Productos activos cuyo stock vendible (lotes sin vencer) está por debajo del mínimo.
@router.get("/stock-bajo", response_model=list[AlertaStockBajo])
def alertas_stock_bajo(
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_ALERTAS)),
):
    stock = func.coalesce(
        func.sum(case((Lote.fecha_vencimiento >= hoy(), Lote.cantidad), else_=0)), 0
    )
    filas = session.exec(
        select(Producto, stock)
        .outerjoin(Lote, Lote.producto_id == Producto.id_producto)
        .where(Producto.activo.is_(True))
        .group_by(Producto.id_producto)
        .having(stock < Producto.stock_minimo)
        .order_by(Producto.nombre)
    ).all()
    return [
        AlertaStockBajo(
            id_producto=p.id_producto,
            nombre=p.nombre,
            stock=int(s),
            stock_minimo=p.stock_minimo,
            faltante=p.stock_minimo - int(s),
        )
        for p, s in filas
    ]


# Lotes con mercadería que ya venció o que vence dentro de los próximos "dias".
@router.get("/vencimientos", response_model=list[AlertaVencimiento])
def alertas_vencimientos(
    dias: int = Query(default=30, ge=0, le=365),
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_ALERTAS)),
):
    fecha_hoy = hoy()
    filas = session.exec(
        select(Lote, Producto.nombre)
        .join(Producto, Producto.id_producto == Lote.producto_id)
        .where(Lote.cantidad > 0, Lote.fecha_vencimiento <= fecha_hoy + timedelta(days=dias))
        .order_by(Lote.fecha_vencimiento, Lote.id_lote)
    ).all()
    return [
        AlertaVencimiento(
            id_lote=lote.id_lote,
            producto_id=lote.producto_id,
            producto=nombre,
            numero_lote=lote.numero_lote,
            fecha_vencimiento=lote.fecha_vencimiento,
            cantidad=lote.cantidad,
            dias_restantes=(lote.fecha_vencimiento - fecha_hoy).days,
            estado="vencido" if lote.fecha_vencimiento < fecha_hoy else "por_vencer",
        )
        for lote, nombre in filas
    ]