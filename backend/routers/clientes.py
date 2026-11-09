from fastapi import APIRouter, Depends, HTTPException, Path
from sqlmodel import Session, select

from comun import CLIENTE_NO_ENCONTRADO, guardar_o_409
from db import get_session
from dependencias import requiere_rol
from models import Cliente
from roles import ROLES_OPERATIVOS
from schemas_clientes import PATRON_DNI, ClienteCrear, ClienteRespuesta

router = APIRouter(prefix="/clientes", tags=["clientes"])

# Los busca y los da de alta quien registra la venta; el dueño no vende, así que no interviene.
ROLES_CLIENTES = ROLES_OPERATIVOS


@router.get("/dni/{dni}", response_model=ClienteRespuesta)
def buscar_por_dni(
    dni: str = Path(pattern=PATRON_DNI),
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_CLIENTES)),
):
    cliente = session.exec(select(Cliente).where(Cliente.dni == dni)).first()
    if cliente is None:
        raise HTTPException(status_code=404, detail=CLIENTE_NO_ENCONTRADO)
    return cliente


# Alta rápida para la venta con cobertura: el DNI es único y lo garantiza la base, también ante dos pedidos a la vez.
@router.post("", response_model=ClienteRespuesta, status_code=201)
def crear_cliente(
    datos: ClienteCrear,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_CLIENTES)),
):
    return guardar_o_409(session, Cliente(**datos.model_dump()), "Ya existe un cliente con ese DNI")
