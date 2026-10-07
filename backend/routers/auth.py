from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from db import get_session
from dependencias import obtener_usuario_actual, obtener_usuario_para_cambio, requiere_rol
from models import Empleado, Usuario
from schemas_auth import CambiarContrasenaPropia, LoginRequest, LoginResponse
from security import crear_token, hashear_contrasena, verificar_contrasena

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(datos: LoginRequest, session: Session = Depends(get_session)):
    mensaje_error = "Usuario o contraseña incorrectos"

    usuario = session.exec(
        select(Usuario).where(Usuario.nombre_usuario == datos.nombreUsuario)
    ).first()

    if usuario is None or not verificar_contrasena(datos.contrasena, usuario.contrasena_hash):
        raise HTTPException(status_code=401, detail=mensaje_error)

    empleado = session.get(Empleado, usuario.empleado_id)

    if not usuario.activo or not empleado.activo:
        raise HTTPException(status_code=401, detail=mensaje_error)

    usuario.ultimo_login = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(usuario)
    session.commit()

    token = crear_token(usuario.nombre_usuario, empleado.rol, usuario.debe_cambiar_contrasena)

    return LoginResponse(
        token=token,
        nombre=empleado.nombre,
        rol=empleado.rol,
        debeCambiarContrasena=usuario.debe_cambiar_contrasena,
    )


@router.get("/me")
def quien_soy(usuario: dict = Depends(obtener_usuario_para_cambio)):
    return usuario


@router.post("/refresh", response_model=LoginResponse)
def refrescar_token(
    usuario: dict = Depends(obtener_usuario_actual),
    session: Session = Depends(get_session),
):
    usuario_db = session.exec(
        select(Usuario).where(Usuario.nombre_usuario == usuario["sub"])
    ).first()
    if usuario_db is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    empleado = session.get(Empleado, usuario_db.empleado_id)

    if not usuario_db.activo or not empleado.activo:
        raise HTTPException(status_code=401, detail="Usuario inactivo")

    nuevo_token = crear_token(usuario_db.nombre_usuario, empleado.rol, usuario_db.debe_cambiar_contrasena)

    return LoginResponse(
        token=nuevo_token,
        nombre=empleado.nombre,
        rol=empleado.rol,
        debeCambiarContrasena=usuario_db.debe_cambiar_contrasena,
    )


# Cambio de contraseña propio: cualquier rol logueado, incluso con el cambio forzado pendiente.
# Devuelve un token nuevo, ya sin la marca de cambio pendiente.
@router.patch("/contrasena", response_model=LoginResponse)
def cambiar_contrasena_propia(
    datos: CambiarContrasenaPropia,
    usuario: dict = Depends(obtener_usuario_para_cambio),
    session: Session = Depends(get_session),
):
    usuario_db = session.exec(
        select(Usuario).where(Usuario.nombre_usuario == usuario["sub"])
    ).first()
    if usuario_db is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    if not verificar_contrasena(datos.contrasena_actual, usuario_db.contrasena_hash):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")
    if datos.contrasena_actual == datos.contrasena_nueva:
        raise HTTPException(status_code=400, detail="La contraseña nueva debe ser distinta de la actual")

    usuario_db.contrasena_hash = hashear_contrasena(datos.contrasena_nueva)
    usuario_db.debe_cambiar_contrasena = False
    session.add(usuario_db)
    session.commit()

    empleado = session.get(Empleado, usuario_db.empleado_id)
    token = crear_token(usuario_db.nombre_usuario, empleado.rol)

    return LoginResponse(token=token, nombre=empleado.nombre, rol=empleado.rol)


# Endpoint de PRUEBA para demostrar requiere_rol; eliminar antes de desplegar.
@router.get("/solo-dueno")
def solo_dueno(usuario: dict = Depends(requiere_rol("dueno"))):
    return {"mensaje": "Tenés acceso", "usuario": usuario}
