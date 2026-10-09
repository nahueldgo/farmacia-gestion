from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, func


from db import get_session
from models import (
    Laboratorio, PrincipioActivo, CondicionIva,
    FormaFarmaceutica, ClaseTerapeutica, CategoriaCoberturaObraSocial,
)
from schemas_catalogos import CondicionIvaRespuesta, CatalogoCrear
from dependencias import obtener_usuario_actual, requiere_rol
from roles import Rol
from routers.productos import router as productos_router
from routers.medicamentos import router as medicamentos_router
from routers.auth import router as auth_router
from routers.empleados import router as empleados_router
from routers.lotes import router as lotes_router
from routers.laboratorios import router as laboratorios_router
from routers.principios_activos import router as principios_activos_router
from routers.alertas import router as alertas_router

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
app.include_router(auth_router)
app.include_router(empleados_router)
app.include_router(lotes_router)
app.include_router(laboratorios_router)
app.include_router(principios_activos_router)
app.include_router(alertas_router)


@app.get("/")
def status():
    return {"status": "ok", "mensaje": "Backend funcionando"}


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
