from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from db import get_session
from dependencias import obtener_usuario_actual
from models import (
    CategoriaCoberturaObraSocial, ClaseTerapeutica, CondicionIva, FormaFarmaceutica,
)
from schemas_catalogos import CondicionIvaRespuesta

router = APIRouter(prefix="/catalogos", tags=["catálogos"])


# Catálogos precargados para los selectores: los puede leer cualquier usuario logueado.
@router.get("/condiciones-iva", response_model=list[CondicionIvaRespuesta])
def listar_condiciones_iva(
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    condiciones = session.exec(
        select(CondicionIva).order_by(CondicionIva.id_condicion_iva)
    ).all()
    return [
        CondicionIvaRespuesta(
            id_condicion_iva=c.id_condicion_iva,
            nombre=c.nombre,
            alicuota=float(c.alicuota),
        )
        for c in condiciones
    ]


@router.get("/formas-farmaceuticas", response_model=list[FormaFarmaceutica])
def listar_formas_farmaceuticas(
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    return session.exec(select(FormaFarmaceutica).order_by(FormaFarmaceutica.nombre)).all()


@router.get("/clases-terapeuticas", response_model=list[ClaseTerapeutica])
def listar_clases_terapeuticas(
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    return session.exec(select(ClaseTerapeutica).order_by(ClaseTerapeutica.nombre)).all()


@router.get("/categorias-cobertura", response_model=list[CategoriaCoberturaObraSocial])
def listar_categorias_cobertura(
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    return session.exec(
        select(CategoriaCoberturaObraSocial).order_by(CategoriaCoberturaObraSocial.id_categoria_cobertura_obra_social)
    ).all()
