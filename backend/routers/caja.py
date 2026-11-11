from dataclasses import asdict
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from comun import empleado_del_usuario, guardar_o_409
from db import get_session
from dependencias import obtener_usuario_actual, requiere_rol
from fechas import a_hora_argentina, ahora_utc, hoy
from models import Caja, MovimientoCaja
from roles import ROLES_OPERATIVOS
from schemas_caja import (
    CajaAbrir,
    CajaRespuesta,
    ConsolidadoRespuesta,
    MovimientoCrear,
    MovimientoRespuesta,
    TotalesRespuesta,
    TotalPorMedioPagoRespuesta,
    TotalPorTipoRespuesta,
)
from servicios.caja import Consolidado, consolidar_caja

router = APIRouter(prefix="/caja", tags=["caja"])

ROLES_OPERAN_CAJA = ROLES_OPERATIVOS
YA_HAY_CAJA_ABIERTA = "Ya hay una caja abierta"
NO_HAY_CAJA_ABIERTA = "No hay una caja abierta"


def _caja_abierta(session: Session) -> Optional[Caja]:
    return session.exec(select(Caja).where(Caja.estado == "abierta")).first()


def _caja_abierta_o_404(session: Session) -> Caja:
    caja = _caja_abierta(session)
    if caja is None:
        raise HTTPException(status_code=404, detail=NO_HAY_CAJA_ABIERTA)
    return caja


def _respuesta(caja: Caja) -> CajaRespuesta:
    return CajaRespuesta(
        id_caja=caja.id_caja,
        fecha=caja.fecha,
        empleado_apertura_id=caja.empleado_apertura_id,
        hora_apertura=a_hora_argentina(caja.hora_apertura),
        monto_apertura=caja.monto_apertura,
        estado=caja.estado,
    )


def _movimiento_respuesta(movimiento: MovimientoCaja) -> MovimientoRespuesta:
    return MovimientoRespuesta(
        id_movimiento_caja=movimiento.id_movimiento_caja,
        caja_id=movimiento.caja_id,
        empleado_id=movimiento.empleado_id,
        tipo=movimiento.tipo,
        monto=movimiento.monto,
        motivo=movimiento.motivo,
        hora=a_hora_argentina(movimiento.hora),
    )


def _consolidado_respuesta(caja: Caja, consolidado: Consolidado) -> ConsolidadoRespuesta:
    return ConsolidadoRespuesta(
        caja=_respuesta(caja),
        ventas=TotalesRespuesta(**asdict(consolidado.ventas)),
        por_tipo=[TotalPorTipoRespuesta(tipo=tipo, **asdict(totales)) for tipo, totales in consolidado.por_tipo.items()],
        por_medio_pago=[
            TotalPorMedioPagoRespuesta(medio_pago=medio, **asdict(totales))
            for medio, totales in consolidado.por_medio_pago.items()
        ],
        total_ingresos=consolidado.total_ingresos,
        total_retiros=consolidado.total_retiros,
        movimientos=[_movimiento_respuesta(m) for m in consolidado.movimientos],
        efectivo_esperado=consolidado.efectivo_esperado,
    )


# Sin una caja abierta no se puede vender (venta.caja_id es obligatorio). El cierre va en el Módulo 5.
@router.post("/abrir", response_model=CajaRespuesta, status_code=201)
def abrir_caja(
    datos: CajaAbrir,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_OPERAN_CAJA)),
):
    if _caja_abierta(session):
        raise HTTPException(status_code=409, detail=YA_HAY_CAJA_ABIERTA)

    caja = Caja(
        fecha=hoy(),
        empleado_apertura_id=empleado_del_usuario(session, usuario),
        hora_apertura=ahora_utc(),
        monto_apertura=Decimal(str(datos.monto_apertura)),
    )
    # Dos pedidos a la vez: el índice único de la base deja pasar solo uno.
    return _respuesta(guardar_o_409(session, caja, YA_HAY_CAJA_ABIERTA))


@router.get("/actual", response_model=CajaRespuesta)
def caja_actual(
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    return _respuesta(_caja_abierta_o_404(session))


# Ingreso o retiro manual de efectivo en la caja abierta (por ejemplo, devolver el dinero de una venta anulada).
@router.post("/movimientos", response_model=MovimientoRespuesta, status_code=201)
def registrar_movimiento(
    datos: MovimientoCrear,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_OPERAN_CAJA)),
):
    caja = _caja_abierta(session)
    if caja is None:
        raise HTTPException(status_code=409, detail=f"{NO_HAY_CAJA_ABIERTA}: abrila antes de registrar el movimiento")

    movimiento = MovimientoCaja(
        caja_id=caja.id_caja,
        empleado_id=empleado_del_usuario(session, usuario),
        tipo=datos.tipo.value,
        monto=datos.monto,
        motivo=datos.motivo,
    )
    session.add(movimiento)
    session.commit()
    session.refresh(movimiento)
    return _movimiento_respuesta(movimiento)


@router.get("/actual/consolidado", response_model=ConsolidadoRespuesta)
def consolidado_actual(
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    caja = _caja_abierta_o_404(session)
    return _consolidado_respuesta(caja, consolidar_caja(session, caja))
