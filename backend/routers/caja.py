from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from comun import empleado_del_usuario
from db import get_session
from dependencias import obtener_usuario_actual, requiere_rol
from fechas import a_hora_argentina, ahora_utc, hoy
from models import Caja
from roles import Rol
from schemas_caja import CajaAbrir, CajaRespuesta

router = APIRouter(prefix="/caja", tags=["caja"])

ROLES_OPERAN_CAJA = (Rol.FARMACEUTICO, Rol.AUXILIAR)


def _caja_abierta(session: Session) -> Optional[Caja]:
    return session.exec(select(Caja).where(Caja.estado == "abierta")).first()


def _respuesta(caja: Caja) -> CajaRespuesta:
    return CajaRespuesta(
        id_caja=caja.id_caja,
        fecha=caja.fecha,
        empleado_apertura_id=caja.empleado_apertura_id,
        hora_apertura=a_hora_argentina(caja.hora_apertura),
        monto_apertura=caja.monto_apertura,
        estado=caja.estado,
    )


# Sin una caja abierta no se puede vender (venta.caja_id es obligatorio). El cierre va en el Módulo 5.
@router.post("/abrir", response_model=CajaRespuesta, status_code=201)
def abrir_caja(
    datos: CajaAbrir,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_OPERAN_CAJA)),
):
    if _caja_abierta(session):
        raise HTTPException(status_code=409, detail="Ya hay una caja abierta")

    caja = Caja(
        fecha=hoy(),
        empleado_apertura_id=empleado_del_usuario(session, usuario),
        hora_apertura=ahora_utc(),
        monto_apertura=Decimal(str(datos.monto_apertura)),
    )
    session.add(caja)
    try:
        session.commit()
    except IntegrityError:
        # Dos pedidos a la vez: el índice único de la base deja pasar solo uno.
        session.rollback()
        raise HTTPException(status_code=409, detail="Ya hay una caja abierta")
    session.refresh(caja)
    return _respuesta(caja)


@router.get("/actual", response_model=CajaRespuesta)
def caja_actual(
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    caja = _caja_abierta(session)
    if caja is None:
        raise HTTPException(status_code=404, detail="No hay una caja abierta")
    return _respuesta(caja)
