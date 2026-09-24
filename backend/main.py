from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select


from db import get_session
from models import Empleado, Usuario
from security import crear_token, verificar_contrasena
from dependencias import obtener_usuario_actual, requiere_rol

app = FastAPI(title="Sistema de Gestión Farmacia - API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    nombreUsuario: str
    contrasena: str

class LoginResponse(BaseModel):
    token: str
    nombre: str
    rol: str

@app.get("/")
def status():
    return {"status": "ok", "mensaje": "Backend funcionando"}

@app.post("/auth/login", response_model=LoginResponse)
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

    token = crear_token(usuario.nombre_usuario, empleado.rol)

    return LoginResponse(token=token, nombre=empleado.nombre, rol=empleado.rol)

@app.get("/auth/me")
def quien_soy(usuario: dict = Depends(obtener_usuario_actual)):
    return usuario

@app.post("/auth/refresh", response_model=LoginResponse)
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

    nuevo_token = crear_token(usuario_db.nombre_usuario, empleado.rol)

    return LoginResponse(token=nuevo_token, nombre=empleado.nombre, rol=empleado.rol)

@app.get("/auth/solo-dueno")
def solo_dueno(usuario: dict = Depends(requiere_rol("dueno"))):
    return {"mensaje": "Tenés acceso", "usuario": usuario}

