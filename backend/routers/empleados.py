from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from db import get_session
from dependencias import requiere_rol
from models import Empleado, Usuario
from roles import Rol
from schemas_empleados import EmpleadoCrear, EmpleadoRespuesta, CambiarContrasena
from security import hashear_contrasena

router = APIRouter(prefix="/empleados", tags=["empleados"])


def _buscar_empleado(session: Session, id_empleado: int) -> Empleado:
    empleado = session.get(Empleado, id_empleado)
    if empleado is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return empleado


def _usuario_de(session: Session, empleado: Empleado) -> Optional[Usuario]:
    return session.exec(
        select(Usuario).where(Usuario.empleado_id == empleado.id_empleado)
    ).first()


def _respuesta(empleado: Empleado, usuario_emp: Optional[Usuario]) -> EmpleadoRespuesta:
    return EmpleadoRespuesta(
        id_empleado=empleado.id_empleado,
        nombre=empleado.nombre,
        apellido=empleado.apellido,
        dni=empleado.dni,
        rol=empleado.rol,
        matricula_profesional=empleado.matricula_profesional,
        fecha_ingreso=empleado.fecha_ingreso,
        activo=empleado.activo,
        nombre_usuario=usuario_emp.nombre_usuario if usuario_emp else "",
        email=usuario_emp.email if usuario_emp else "",
    )


# Alta atómica: empleado y usuario en una sola transacción.
@router.post("", response_model=EmpleadoRespuesta, status_code=201)
def crear_empleado(
    datos: EmpleadoCrear,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(Rol.DUENO)),
):
    if session.exec(select(Empleado).where(Empleado.dni == datos.dni)).first():
        raise HTTPException(status_code=409, detail="Ya existe un empleado con ese DNI")
    if session.exec(select(Usuario).where(Usuario.nombre_usuario == datos.nombre_usuario)).first():
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese nombre de usuario")
    if session.exec(select(Usuario).where(Usuario.email == datos.email)).first():
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email")

    empleado = Empleado(
        nombre=datos.nombre,
        apellido=datos.apellido,
        dni=datos.dni,
        rol=datos.rol.value,
        matricula_profesional=datos.matricula_profesional,
        fecha_ingreso=datos.fecha_ingreso,
    )
    session.add(empleado)
    session.flush()  # asigna id_empleado sin cerrar la transacción

    nuevo_usuario = Usuario(
        empleado_id=empleado.id_empleado,
        nombre_usuario=datos.nombre_usuario,
        email=datos.email,
        contrasena_hash=hashear_contrasena(datos.contrasena),
    )
    session.add(nuevo_usuario)
    session.commit()
    session.refresh(empleado)
    session.refresh(nuevo_usuario)

    return _respuesta(empleado, nuevo_usuario)


@router.get("", response_model=list[EmpleadoRespuesta])
def listar_empleados(
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(Rol.DUENO)),
):
    empleados = session.exec(select(Empleado)).all()
    return [_respuesta(e, _usuario_de(session, e)) for e in empleados]


@router.get("/{id_empleado}", response_model=EmpleadoRespuesta)
def obtener_empleado(
    id_empleado: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(Rol.DUENO)),
):
    empleado = _buscar_empleado(session, id_empleado)
    return _respuesta(empleado, _usuario_de(session, empleado))


# Baja: desactiva al empleado y a su usuario juntos.
@router.patch("/{id_empleado}/baja", response_model=EmpleadoRespuesta)
def dar_de_baja_empleado(
    id_empleado: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(Rol.DUENO)),
):
    empleado = _buscar_empleado(session, id_empleado)
    usuario_emp = _usuario_de(session, empleado)

    empleado.activo = False
    session.add(empleado)
    if usuario_emp is not None:
        usuario_emp.activo = False
        session.add(usuario_emp)
    session.commit()
    session.refresh(empleado)

    return _respuesta(empleado, usuario_emp)


# Reactiva los dos, en espejo con la baja.
@router.patch("/{id_empleado}/reactivar", response_model=EmpleadoRespuesta)
def reactivar_empleado(
    id_empleado: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(Rol.DUENO)),
):
    empleado = _buscar_empleado(session, id_empleado)
    usuario_emp = _usuario_de(session, empleado)

    empleado.activo = True
    session.add(empleado)
    if usuario_emp is not None:
        usuario_emp.activo = True
        session.add(usuario_emp)
    session.commit()
    session.refresh(empleado)

    return _respuesta(empleado, usuario_emp)


@router.patch("/{id_empleado}/contrasena", response_model=EmpleadoRespuesta)
def cambiar_contrasena_empleado(
    id_empleado: int,
    datos: CambiarContrasena,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(Rol.DUENO)),
):
    empleado = _buscar_empleado(session, id_empleado)
    usuario_emp = _usuario_de(session, empleado)
    if usuario_emp is None:
        raise HTTPException(status_code=404, detail="El empleado no tiene un usuario asociado")

    usuario_emp.contrasena_hash = hashear_contrasena(datos.contrasena_nueva)
    session.add(usuario_emp)
    session.commit()
    session.refresh(empleado)

    return _respuesta(empleado, usuario_emp)
