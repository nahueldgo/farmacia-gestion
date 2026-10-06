from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func

from db import get_session
from dependencias import requiere_rol
from models import Producto, Laboratorio, CondicionIva
from roles import Rol
from schemas_productos import ProductoCrear, ProductoRespuesta

router = APIRouter(prefix="/productos", tags=["productos"])

TIPOS_PRODUCTO = ("medicamento", "perfumeria", "cuidado_personal", "otro")
ROLES_ALTA_PRODUCTO = (Rol.FARMACEUTICO, Rol.AUXILIAR)


@router.post("", response_model=ProductoRespuesta, status_code=201)
def crear_producto(
    datos: ProductoCrear,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_ALTA_PRODUCTO)),
):
    nombre = datos.nombre.strip()
    if not nombre:
        raise HTTPException(status_code=422, detail="El nombre no puede estar vacío")
    if datos.tipo_producto not in TIPOS_PRODUCTO:
        raise HTTPException(status_code=422, detail="Tipo de producto inválido")
    if datos.tipo_producto == "medicamento" and datos.laboratorio_id is None:
        raise HTTPException(status_code=422, detail="Un medicamento necesita laboratorio")

    if session.get(CondicionIva, datos.condicion_iva_id) is None:
        raise HTTPException(status_code=404, detail="No existe esa condición de IVA")

    if datos.laboratorio_id is not None:
        laboratorio = session.get(Laboratorio, datos.laboratorio_id)
        if laboratorio is None:
            raise HTTPException(status_code=404, detail="No existe ese laboratorio")
        if not laboratorio.activo:
            raise HTTPException(status_code=409, detail="El laboratorio está dado de baja")

    repetido = session.exec(
        select(Producto).where(
            func.lower(Producto.nombre) == nombre.lower(),
            Producto.laboratorio_id == datos.laboratorio_id,
        )
    ).first()
    if repetido:
        raise HTTPException(status_code=409, detail="Ya existe un producto con ese nombre y laboratorio")

    producto = Producto(
        nombre=nombre,
        descripcion=datos.descripcion,
        laboratorio_id=datos.laboratorio_id,
        precio=Decimal(str(datos.precio)),
        condicion_iva_id=datos.condicion_iva_id,
        tipo_producto=datos.tipo_producto,
        stock_minimo=datos.stock_minimo,
    )
    session.add(producto)
    session.commit()
    session.refresh(producto)
    return producto
