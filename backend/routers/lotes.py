from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select

from db import get_session
from dependencias import obtener_usuario_actual, requiere_rol
from models import Lote, Producto
from roles import Rol
from schemas_lotes import LoteCrear, LoteRespuesta

router = APIRouter(tags=["lotes"])

ROLES_ALTA_LOTE = (Rol.FARMACEUTICO, Rol.AUXILIAR)


def _producto_activo(session: Session, id_producto: int) -> Producto:
    producto = session.get(Producto, id_producto)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if not producto.activo:
        raise HTTPException(status_code=409, detail="El producto está dado de baja")
    return producto


@router.post("/productos/{id_producto}/lotes", response_model=LoteRespuesta, status_code=201)
def crear_lote(
    id_producto: int,
    datos: LoteCrear,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_ALTA_LOTE)),
):
    _producto_activo(session, id_producto)

    # El número de lote no se repite dentro del mismo producto.
    repetido = session.exec(
        select(Lote).where(
            Lote.producto_id == id_producto,
            func.lower(Lote.numero_lote) == datos.numero_lote.lower(),
        )
    ).first()
    if repetido:
        raise HTTPException(status_code=409, detail="Ya existe un lote con ese número para este producto")

    lote = Lote(
        producto_id=id_producto,
        numero_lote=datos.numero_lote,
        fecha_vencimiento=datos.fecha_vencimiento,
        cantidad=datos.cantidad,
    )
    session.add(lote)
    session.commit()
    session.refresh(lote)
    return lote


@router.get("/productos/{id_producto}/lotes", response_model=list[LoteRespuesta])
def listar_lotes(
    id_producto: int,
    incluir_agotados: bool = False,
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    if session.get(Producto, id_producto) is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    consulta = select(Lote).where(Lote.producto_id == id_producto)
    if not incluir_agotados:
        consulta = consulta.where(Lote.cantidad > 0)
    # Primero el que vence antes (FEFO).
    return session.exec(consulta.order_by(Lote.fecha_vencimiento, Lote.id_lote)).all()
