from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from comun import nombre_limpio, obtener_o_404, verificar_nombre_libre
from db import get_session
from dependencias import obtener_usuario_actual, requiere_rol
from models import Laboratorio
from roles import Rol
from schemas_catalogos import CatalogoCrear

router = APIRouter(prefix="/catalogos/laboratorios", tags=["laboratorios"])

# El alta la puede hacer cualquier rol operativo.
ROLES_ALTA_LABORATORIO = (Rol.FARMACEUTICO, Rol.AUXILIAR, Rol.DUENO)
ROLES_EDICION_LABORATORIO = (Rol.FARMACEUTICO,)


def _buscar_laboratorio(session: Session, id_laboratorio: int) -> Laboratorio:
    return obtener_o_404(session, Laboratorio, id_laboratorio, "Laboratorio no encontrado")


# Para el selector: solo los activos, y los puede leer cualquier usuario logueado.
@router.get("", response_model=list[Laboratorio])
def listar_laboratorios(
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    return session.exec(
        select(Laboratorio).where(Laboratorio.activo.is_(True)).order_by(Laboratorio.nombre)
    ).all()


@router.post("", response_model=Laboratorio, status_code=201)
def crear_laboratorio(
    datos: CatalogoCrear,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_ALTA_LABORATORIO)),
):
    nombre = nombre_limpio(datos.nombre)
    verificar_nombre_libre(
        session, Laboratorio, Laboratorio.id_laboratorio, nombre, "Ya existe un laboratorio con ese nombre"
    )

    laboratorio = Laboratorio(nombre=nombre)
    session.add(laboratorio)
    session.commit()
    session.refresh(laboratorio)
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

    nombre = nombre_limpio(datos.nombre)
    verificar_nombre_libre(
        session, Laboratorio, Laboratorio.id_laboratorio, nombre,
        "Ya existe un laboratorio con ese nombre", id_propio=id_laboratorio,
    )

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
