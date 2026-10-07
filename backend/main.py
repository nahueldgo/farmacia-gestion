from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select, func

from db import get_session
from models import (
    Empleado, Usuario, Laboratorio, PrincipioActivo, CondicionIva,
    FormaFarmaceutica, ClaseTerapeutica, CategoriaCoberturaObraSocial,
)
from schemas_catalogos import CondicionIvaRespuesta, CatalogoCrear
from security import crear_token, verificar_contrasena, hashear_contrasena
from dependencias import obtener_usuario_actual, requiere_rol
from roles import Rol
from schemas_empleados import EmpleadoCrear, EmpleadoRespuesta, CambiarContrasena
from routers.productos import router as productos_router
from routers.medicamentos import router as medicamentos_router

app = FastAPI(title="Sistema de Gestión Farmacia - API")

# TEMPORAL: allow_origins="*" solo para desarrollo; restringir a los orígenes reales antes de desplegar.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(productos_router)
app.include_router(medicamentos_router)

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

# Endpoint de PRUEBA para demostrar requiere_rol; eliminar cuando haya un endpoint real con rol o antes de desplegar.
@app.get("/auth/solo-dueno")
def solo_dueno(usuario: dict = Depends(requiere_rol("dueno"))):
    return {"mensaje": "Tenés acceso", "usuario": usuario}


# Alta atómica: empleado y usuario en una sola transacción.
@app.post("/empleados", response_model=EmpleadoRespuesta, status_code=201)
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

    return EmpleadoRespuesta(
        id_empleado=empleado.id_empleado,
        nombre=empleado.nombre,
        apellido=empleado.apellido,
        dni=empleado.dni,
        rol=empleado.rol,
        matricula_profesional=empleado.matricula_profesional,
        fecha_ingreso=empleado.fecha_ingreso,
        activo=empleado.activo,
        nombre_usuario=nuevo_usuario.nombre_usuario,
        email=nuevo_usuario.email,
    )
@app.get("/empleados", response_model=list[EmpleadoRespuesta])
def listar_empleados(
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(Rol.DUENO)),
):
    empleados = session.exec(select(Empleado)).all()
    respuesta = []
    for empleado in empleados:
        usuario_emp = session.exec(
            select(Usuario).where(Usuario.empleado_id == empleado.id_empleado)
        ).first()
        respuesta.append(EmpleadoRespuesta(
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
        ))
    return respuesta


@app.get("/empleados/{id_empleado}", response_model=EmpleadoRespuesta)
def obtener_empleado(
    id_empleado: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(Rol.DUENO)),
):
    empleado = session.get(Empleado, id_empleado)
    if empleado is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    usuario_emp = session.exec(
        select(Usuario).where(Usuario.empleado_id == empleado.id_empleado)
    ).first()

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
# Baja: desactiva al empleado y a su usuario juntos.
@app.patch("/empleados/{id_empleado}/baja", response_model=EmpleadoRespuesta)
def dar_de_baja_empleado(
    id_empleado: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(Rol.DUENO)),
):
    empleado = session.get(Empleado, id_empleado)
    if empleado is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    usuario_emp = session.exec(
        select(Usuario).where(Usuario.empleado_id == empleado.id_empleado)
    ).first()

    empleado.activo = False
    session.add(empleado)
    if usuario_emp is not None:
        usuario_emp.activo = False
        session.add(usuario_emp)
    session.commit()
    session.refresh(empleado)

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


# Reactiva los dos, en espejo con la baja.
@app.patch("/empleados/{id_empleado}/reactivar", response_model=EmpleadoRespuesta)
def reactivar_empleado(
    id_empleado: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(Rol.DUENO)),
):
    empleado = session.get(Empleado, id_empleado)
    if empleado is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    usuario_emp = session.exec(
        select(Usuario).where(Usuario.empleado_id == empleado.id_empleado)
    ).first()

    empleado.activo = True
    session.add(empleado)
    if usuario_emp is not None:
        usuario_emp.activo = True
        session.add(usuario_emp)
    session.commit()
    session.refresh(empleado)

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
@app.patch("/empleados/{id_empleado}/contrasena", response_model=EmpleadoRespuesta)
def cambiar_contrasena_empleado(
    id_empleado: int,
    datos: CambiarContrasena,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(Rol.DUENO)),
):
    empleado = session.get(Empleado, id_empleado)
    if empleado is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    usuario_emp = session.exec(
        select(Usuario).where(Usuario.empleado_id == empleado.id_empleado)
    ).first()
    if usuario_emp is None:
        raise HTTPException(status_code=404, detail="El empleado no tiene un usuario asociado")

    usuario_emp.contrasena_hash = hashear_contrasena(datos.contrasena_nueva)
    session.add(usuario_emp)
    session.commit()
    session.refresh(empleado)

    return EmpleadoRespuesta(
        id_empleado=empleado.id_empleado,
        nombre=empleado.nombre,
        apellido=empleado.apellido,
        dni=empleado.dni,
        rol=empleado.rol,
        matricula_profesional=empleado.matricula_profesional,
        fecha_ingreso=empleado.fecha_ingreso,
        activo=empleado.activo,
        nombre_usuario=usuario_emp.nombre_usuario,
        email=usuario_emp.email,
    )
# Catálogos para los selectores: los puede leer cualquier usuario logueado.
@app.get("/catalogos/laboratorios", response_model=list[Laboratorio])
def listar_laboratorios(
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    # Solo activos.
    return session.exec(
        select(Laboratorio).where(Laboratorio.activo.is_(True)).order_by(Laboratorio.nombre)
    ).all()


@app.get("/catalogos/principios-activos", response_model=list[PrincipioActivo])
def listar_principios_activos(
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    return session.exec(select(PrincipioActivo).order_by(PrincipioActivo.nombre)).all()


@app.get("/catalogos/condiciones-iva", response_model=list[CondicionIvaRespuesta])
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


@app.get("/catalogos/formas-farmaceuticas", response_model=list[FormaFarmaceutica])
def listar_formas_farmaceuticas(
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    return session.exec(select(FormaFarmaceutica).order_by(FormaFarmaceutica.nombre)).all()


@app.get("/catalogos/clases-terapeuticas", response_model=list[ClaseTerapeutica])
def listar_clases_terapeuticas(
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    return session.exec(select(ClaseTerapeutica).order_by(ClaseTerapeutica.nombre)).all()


@app.get("/catalogos/categorias-cobertura", response_model=list[CategoriaCoberturaObraSocial])
def listar_categorias_cobertura(
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    return session.exec(
        select(CategoriaCoberturaObraSocial).order_by(CategoriaCoberturaObraSocial.id_categoria_cobertura_obra_social)
    ).all()
# Alta de catálogos: la puede hacer cualquier rol operativo.
ROLES_ALTA_CATALOGO = (Rol.FARMACEUTICO, Rol.AUXILIAR, Rol.DUENO)


@app.post("/catalogos/laboratorios", response_model=Laboratorio, status_code=201)
def crear_laboratorio(
    datos: CatalogoCrear,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_ALTA_CATALOGO)),
):
    nombre = datos.nombre.strip()
    if not nombre:
        raise HTTPException(status_code=422, detail="El nombre no puede estar vacío")
    # Duplicado sin importar mayúsculas ni espacios.
    existente = session.exec(
        select(Laboratorio).where(func.lower(Laboratorio.nombre) == nombre.lower())
    ).first()
    if existente:
        raise HTTPException(status_code=409, detail="Ya existe un laboratorio con ese nombre")

    laboratorio = Laboratorio(nombre=nombre)
    session.add(laboratorio)
    session.commit()
    session.refresh(laboratorio)
    return laboratorio


@app.post("/catalogos/principios-activos", response_model=PrincipioActivo, status_code=201)
def crear_principio_activo(
    datos: CatalogoCrear,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_ALTA_CATALOGO)),
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
