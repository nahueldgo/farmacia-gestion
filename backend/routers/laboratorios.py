from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select

from db import get_session
from dependencias import requiere_rol
from models import Laboratorio
from roles import Rol
from schemas_catalogos import CatalogoCrear

router = APIRouter(prefix="/catalogos/laboratorios", tags=["laboratorios"])

ROLES_EDICION_LABORATORIO = (Rol.FARMACEUTICO,)


def _buscar_laboratorio(session: Session, id_laboratorio: int) -> Laboratorio:
    laboratorio = session.get(Laboratorio, id_laboratorio)
    if laboratorio is None:
        raise HTTPException(status_code=404, detail="Laboratorio no encontrado")
    return laboratorio


# El listado normal solo trae los activos: para reactivar hace falta ver también los de baja.
@router.get("/todos", response_model=list[Laboratorio])
def listar_todos(
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_EDICION_LABORATORIO)),
):
    return session.exec(select(Laboratorio).order_by(Laboratorio.nombre)).all()


@router.patch("/{id_laboratorio}", response_model=Laboratorio)
def renombrar_laboratorio(
    id_laboratorio: int,
    datos: CatalogoCrear,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_EDICION_LABORATORIO)),
):
    laboratorio = _buscar_laboratorio(session, id_laboratorio)

    nombre = datos.nombre.strip()
    if not nombre:
        raise HTTPException(status_code=422, detail="El nombre no puede estar vacío")

    # Duplicado sin importar mayúsculas ni espacios, salvo con él mismo.
    repetido = session.exec(
        select(Laboratorio).where(
            func.lower(Laboratorio.nombre) == nombre.lower(),
            Laboratorio.id_laboratorio != id_laboratorio,
        )
    ).first()
    if repetido:
        raise HTTPException(status_code=409, detail="Ya existe un laboratorio con ese nombre")

    laboratorio.nombre = nombre
    session.add(laboratorio)
    session.commit()
    session.refresh(laboratorio)
    return laboratorio


# Baja lógica: deja de ofrecerse, pero los productos que ya lo usan lo conservan.
@router.patch("/{id_laboratorio}/baja", response_model=Laboratorio)
def dar_de_baja_laboratorio(
    id_laboratorio: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_EDICION_LABORATORIO)),
):
    laboratorio = _buscar_laboratorio(session, id_laboratorio)
    laboratorio.activo = False
    session.add(laboratorio)
    session.commit()
    session.refresh(laboratorio)
    return laboratorio


@router.patch("/{id_laboratorio}/reactivar", response_model=Laboratorio)
def reactivar_laboratorio(
    id_laboratorio: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_EDICION_LABORATORIO)),
):
    laboratorio = _buscar_laboratorio(session, id_laboratorio)
    laboratorio.activo = True
    session.add(laboratorio)
    session.commit()
    session.refresh(laboratorio)
    return laboratorio
