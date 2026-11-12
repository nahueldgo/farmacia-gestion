from dataclasses import asdict
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from comun import empleado_del_usuario, guardar_o_409, obtener_o_404
from db import get_session
from dependencias import obtener_usuario_actual, requiere_rol
from fechas import a_hora_argentina, ahora_utc, hoy
from models import Caja, Empleado, MovimientoCaja
from roles import ROLES_OPERATIVOS
from schemas_caja import (
    CajaAbrir,
    CajaCerrar,
    CajaRespuesta,
    CierreResumen,
    ConsolidadoRespuesta,
    MovimientoCrear,
    MovimientoRespuesta,
    TotalesRespuesta,
    TotalPorMedioPagoRespuesta,
    TotalPorTipoRespuesta,
)
from servicios.base_ventas import RangoDeFechasInvalido
from servicios.caja import (
    Consolidado,
    caja_abierta,
    caja_abierta_para_cerrar,
    caja_abierta_para_operar,
    cerrar_caja,
    cierres_del_periodo,
    consolidar_caja,
)

router = APIRouter(prefix="/caja", tags=["caja"])

ROLES_OPERAN_CAJA = ROLES_OPERATIVOS
YA_HAY_CAJA_ABIERTA = "Ya hay una caja abierta"
NO_HAY_CAJA_ABIERTA = "No hay una caja abierta"
CAJA_NO_ENCONTRADA = "Caja no encontrada"


def _caja_abierta_o_404(session: Session) -> Caja:
    caja = caja_abierta(session)
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
        empleado_cierre_id=caja.empleado_cierre_id,
        hora_cierre=None if caja.hora_cierre is None else a_hora_argentina(caja.hora_cierre),
        monto_cierre_declarado=caja.monto_cierre_declarado,
        monto_cierre_sistema=caja.monto_cierre_sistema,
        diferencia=caja.diferencia,
    )


def _cierre_resumen(caja: Caja, abrio: Empleado, cerro: Empleado) -> CierreResumen:
    return CierreResumen(
        **_respuesta(caja).model_dump(),
        empleado_apertura=f"{abrio.nombre} {abrio.apellido}",
        empleado_cierre=f"{cerro.nombre} {cerro.apellido}",
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


# Sin una caja abierta no se puede vender (venta.caja_id es obligatorio).
@router.post("/abrir", response_model=CajaRespuesta, status_code=201)
def abrir_caja(
    datos: CajaAbrir,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_OPERAN_CAJA)),
):
    if caja_abierta(session):
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
    caja = caja_abierta_para_operar(session)
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


# Cierra la caja abierta con el monto contado. Responde el consolidado final con el arqueo (lo declarado, lo que
# esperaba el sistema y la diferencia), así que la pantalla arma el resumen con una sola llamada.
@router.post("/cerrar", response_model=ConsolidadoRespuesta)
def cerrar_caja_actual(
    datos: CajaCerrar,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_OPERAN_CAJA)),
):
    caja = caja_abierta_para_cerrar(session)
    if caja is None:
        raise HTTPException(status_code=409, detail=f"{NO_HAY_CAJA_ABIERTA}: no hay nada para cerrar")

    consolidado = cerrar_caja(session, caja, empleado_del_usuario(session, usuario), datos.monto_declarado)
    respuesta = _consolidado_respuesta(caja, consolidado)
    session.commit()
    return respuesta


@router.get("/actual/consolidado", response_model=ConsolidadoRespuesta)
def consolidado_actual(
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    caja = _caja_abierta_o_404(session)
    return _consolidado_respuesta(caja, consolidar_caja(session, caja))


# Historial de cierres: las cajas cerradas de un día de Argentina (por defecto, hoy) o de un rango con desde y hasta.
@router.get("/cierres", response_model=list[CierreResumen])
def historial_de_cierres(
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    try:
        filas = cierres_del_periodo(session, desde, hasta)
    except RangoDeFechasInvalido as error:
        raise HTTPException(status_code=error.estado_http, detail=error.mensaje)
    return [_cierre_resumen(caja, abrio, cerro) for caja, abrio, cerro in filas]


# El consolidado de cualquier caja, abierta o cerrada: para ver el detalle de un cierre del historial.
@router.get("/{id_caja}/consolidado", response_model=ConsolidadoRespuesta)
def consolidado_de_una_caja(
    id_caja: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    caja = obtener_o_404(session, Caja, id_caja, CAJA_NO_ENCONTRADA)
    return _consolidado_respuesta(caja, consolidar_caja(session, caja))
