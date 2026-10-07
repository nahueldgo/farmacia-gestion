from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from db import get_session
from dependencias import requiere_rol
from models import Empleado, Usuario
from roles import Rol
from schemas_empleados import CambiarContrasena, EmpleadoCrear, EmpleadoEditar, EmpleadoRespuesta
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


def _id_empleado_logueado(session: Session, usuario: dict) -> Optional[int]:
    actual = session.exec(
        select(Usuario).where(Usuario.nombre_usuario == usuario["sub"])
    ).first()
    return actual.empleado_id if actual else None


# Evita que el sistema se quede sin ningún dueño activo.
def _quedaria_sin_dueno(session: Session, id_empleado: int) -> bool:
    otro = session.exec(
        select(Empleado).where(
            Empleado.rol == Rol.DUENO.value,
            Empleado.activo.is_(True),
            Empleado.id_empleado != id_empleado,
        )
    ).first()
    return otro is None


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
        debe_cambiar_contrasena=True,
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


@router.patch("/{id_empleado}", response_model=EmpleadoRespuesta)
def editar_empleado(
    id_empleado: int,
    datos: EmpleadoEditar,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(Rol.DUENO)),
):
    empleado = _buscar_empleado(session, id_empleado)
    usuario_emp = _usuario_de(session, empleado)
    cambios = datos.model_dump(exclude_unset=True)

    if "rol" in cambios and cambios["rol"] != empleado.rol:
        if empleado.id_empleado == _id_empleado_logueado(session, usuario):
            raise HTTPException(status_code=400, detail="No podés cambiarte el rol a vos mismo")
        if empleado.rol == Rol.DUENO and empleado.activo and _quedaria_sin_dueno(session, empleado.id_empleado):
            raise HTTPException(status_code=409, detail="No se puede cambiar el rol del único dueño activo")

    # La matrícula se controla con el valor final, no solo con lo enviado.
    rol_final = cambios.get("rol", empleado.rol)
    matricula_final = cambios.get("matricula_profesional", empleado.matricula_profesional)
    if rol_final == Rol.FARMACEUTICO and not (matricula_final or "").strip():
        raise HTTPException(status_code=422, detail="El farmacéutico debe tener matrícula profesional")

    # El email vive en el usuario: no puede repetirse con el de otro.
    if "email" in cambios and usuario_emp is not None:
        otro = session.exec(
            select(Usuario).where(
                Usuario.email == cambios["email"],
                Usuario.id_usuario != usuario_emp.id_usuario,
            )
        ).first()
        if otro:
            raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email")
        usuario_emp.email = cambios.pop("email")
        session.add(usuario_emp)
    else:
        cambios.pop("email", None)

    if "rol" in cambios:
        cambios["rol"] = cambios["rol"].value
    for campo, valor in cambios.items():
        setattr(empleado, campo, valor)
    session.add(empleado)
    session.commit()
    session.refresh(empleado)

    return _respuesta(empleado, usuario_emp)


# Baja: desactiva al empleado y a su usuario juntos.
@router.patch("/{id_empleado}/baja", response_model=EmpleadoRespuesta)
def dar_de_baja_empleado(
    id_empleado: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(Rol.DUENO)),
):
    empleado = _buscar_empleado(session, id_empleado)
    if empleado.id_empleado == _id_empleado_logueado(session, usuario):
        raise HTTPException(status_code=400, detail="No podés darte de baja a vos mismo")
    if empleado.rol == Rol.DUENO and empleado.activo and _quedaria_sin_dueno(session, empleado.id_empleado):
        raise HTTPException(status_code=409, detail="No se puede dar de baja al único dueño activo")
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
    usuario_emp.debe_cambiar_contrasena = True  # la clave la conoce el dueño: se cambia al ingresar
    session.add(usuario_emp)
    session.commit()
    session.refresh(empleado)

    return _respuesta(empleado, usuario_emp)
