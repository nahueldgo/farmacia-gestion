from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.productos import router as productos_router
from routers.medicamentos import router as medicamentos_router
from routers.auth import router as auth_router
from routers.empleados import router as empleados_router
from routers.lotes import router as lotes_router
from routers.catalogos import router as catalogos_router
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
app.include_router(catalogos_router)
app.include_router(laboratorios_router)
app.include_router(principios_activos_router)
app.include_router(alertas_router)


@app.get("/")
def status():
    return {"status": "ok", "mensaje": "Backend funcionando"}
