from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, func, select

from db import get_session
from dependencias import obtener_usuario_actual, requiere_rol
from models import Medicamento, PrincipioActivo
from roles import Rol
from schemas_catalogos import CatalogoCrear

router = APIRouter(prefix="/catalogos/principios-activos", tags=["principios activos"])

# El alta la puede hacer cualquier rol operativo.
ROLES_ALTA_PRINCIPIO = (Rol.FARMACEUTICO, Rol.AUXILIAR, Rol.DUENO)
ROLES_EDICION_PRINCIPIO = (Rol.FARMACEUTICO,)


def _buscar_principio(session: Session, id_principio_activo: int) -> PrincipioActivo:
    principio = session.get(PrincipioActivo, id_principio_activo)
    if principio is None:
        raise HTTPException(status_code=404, detail="Principio activo no encontrado")
    return principio


@router.get("", response_model=list[PrincipioActivo])
def listar_principios_activos(
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    return session.exec(select(PrincipioActivo).order_by(PrincipioActivo.nombre)).all()


@router.post("", response_model=PrincipioActivo, status_code=201)
def crear_principio_activo(
    datos: CatalogoCrear,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_ALTA_PRINCIPIO)),
):
    nombre = datos.nombre.strip()
    if not nombre:
        raise HTTPException(status_code=422, detail="El nombre no puede estar vacío")
    existente = session.exec(
        select(PrincipioActivo).where(func.lower(PrincipioActivo.nombre) == nombre.lower())
    ).first()
    if existente:
        raise HTTPException(status_code=409, detail="Ya existe un principio activo con ese nombre")

    principio = PrincipioActivo(nombre=nombre)
    session.add(principio)
    session.commit()
    session.refresh(principio)
    return principio


@router.patch("/{id_principio_activo}", response_model=PrincipioActivo)
def renombrar_principio_activo(
    id_principio_activo: int,
    datos: CatalogoCrear,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_EDICION_PRINCIPIO)),
):
    principio = _buscar_principio(session, id_principio_activo)

    nombre = datos.nombre.strip()
    if not nombre:
        raise HTTPException(status_code=422, detail="El nombre no puede estar vacío")

    # Duplicado sin importar mayúsculas ni espacios, salvo con él mismo.
    repetido = session.exec(
        select(PrincipioActivo).where(
            func.lower(PrincipioActivo.nombre) == nombre.lower(),
            PrincipioActivo.id_principio_activo != id_principio_activo,
        )
    ).first()
    if repetido:
        raise HTTPException(status_code=409, detail="Ya existe un principio activo con ese nombre")

    principio.nombre = nombre
    session.add(principio)
    session.commit()
    session.refresh(principio)
    return principio


# Se borra de verdad, pero solo si ningún medicamento lo usa.
@router.delete("/{id_principio_activo}", status_code=204)
def borrar_principio_activo(
    id_principio_activo: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_EDICION_PRINCIPIO)),
):
    principio = _buscar_principio(session, id_principio_activo)

    en_uso = session.exec(
        select(Medicamento).where(Medicamento.principio_activo_id == id_principio_activo)
    ).first()
    if en_uso:
        raise HTTPException(status_code=409, detail="No se puede borrar: lo usan medicamentos")

    session.delete(principio)
    session.commit()
    return Response(status_code=204)
