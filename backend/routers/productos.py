from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func

from db import get_session
from dependencias import obtener_usuario_actual, requiere_rol
from fechas import hoy
from models import Producto, Laboratorio, CondicionIva, Medicamento, Lote
from roles import Rol
from schemas_productos import ProductoCrear, ProductoEditar, ProductoRespuesta


router = APIRouter(prefix="/productos", tags=["productos"])

TIPOS_PRODUCTO = ("medicamento", "perfumeria", "cuidado_personal", "otro")
ROLES_ALTA_PRODUCTO = (Rol.FARMACEUTICO, Rol.AUXILIAR)
ROLES_EDICION_PRODUCTO = (Rol.FARMACEUTICO,)


# Stock vendible: suma de los lotes que todavía no vencieron.
def _stock_de(session: Session, ids: list[int]) -> dict[int, int]:
    if not ids:
        return {}
    filas = session.exec(
        select(Lote.producto_id, func.sum(Lote.cantidad))
        .where(Lote.producto_id.in_(ids), Lote.fecha_vencimiento >= hoy())
        .group_by(Lote.producto_id)
    ).all()
    return {producto_id: int(total) for producto_id, total in filas}


def _con_stock(session: Session, producto: Producto) -> ProductoRespuesta:
    stock = _stock_de(session, [producto.id_producto]).get(producto.id_producto, 0)
    return ProductoRespuesta(**producto.model_dump(), stock=stock)


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
    return _con_stock(session, producto)


@router.get("", response_model=list[ProductoRespuesta])
def listar_productos(
    buscar: Optional[str] = None,
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    consulta = select(Producto).where(Producto.activo.is_(True))
    if buscar:
        # Búsqueda por parte del nombre, sin distinguir mayúsculas.
        consulta = consulta.where(Producto.nombre.ilike(f"%{buscar.strip()}%"))
    productos = session.exec(consulta.order_by(Producto.nombre)).all()
    # El stock de todos se calcula en una sola consulta.
    stocks = _stock_de(session, [p.id_producto for p in productos])
    return [
        ProductoRespuesta(**p.model_dump(), stock=stocks.get(p.id_producto, 0))
        for p in productos
    ]


@router.get("/{id_producto}", response_model=ProductoRespuesta)
def obtener_producto(
    id_producto: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    producto = session.get(Producto, id_producto)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return _con_stock(session, producto)


def _buscar_producto(session: Session, id_producto: int) -> Producto:
    producto = session.get(Producto, id_producto)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@router.patch("/{id_producto}", response_model=ProductoRespuesta)
def editar_producto(
    id_producto: int,
    datos: ProductoEditar,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_EDICION_PRODUCTO)),
):
    producto = _buscar_producto(session, id_producto)
    # Solo los campos que vinieron en el pedido.
    cambios = datos.model_dump(exclude_unset=True)

    for campo in ("nombre", "precio", "condicion_iva_id", "tipo_producto", "stock_minimo"):
        if campo in cambios and cambios[campo] is None:
            raise HTTPException(status_code=422, detail=f"El campo {campo} no puede ser nulo")
    if "nombre" in cambios:
        cambios["nombre"] = cambios["nombre"].strip()
        if not cambios["nombre"]:
            raise HTTPException(status_code=422, detail="El nombre no puede estar vacío")

    # Cómo quedaría el producto, para validar las reglas sobre el resultado final.
    final = {
        "nombre": producto.nombre,
        "laboratorio_id": producto.laboratorio_id,
        "tipo_producto": producto.tipo_producto,
        **cambios,
    }
    if final["tipo_producto"] not in TIPOS_PRODUCTO:
        raise HTTPException(status_code=422, detail="Tipo de producto inválido")
    if final["tipo_producto"] == "medicamento" and final["laboratorio_id"] is None:
        raise HTTPException(status_code=422, detail="Un medicamento necesita laboratorio")
    if final["tipo_producto"] != "medicamento" and session.get(Medicamento, id_producto) is not None:
        raise HTTPException(status_code=409, detail="El producto tiene datos de medicamento: no puede cambiar de tipo")

    if "condicion_iva_id" in cambios and session.get(CondicionIva, cambios["condicion_iva_id"]) is None:
        raise HTTPException(status_code=404, detail="No existe esa condición de IVA")
    if cambios.get("laboratorio_id") is not None:
        laboratorio = session.get(Laboratorio, cambios["laboratorio_id"])
        if laboratorio is None:
            raise HTTPException(status_code=404, detail="No existe ese laboratorio")
        if not laboratorio.activo:
            raise HTTPException(status_code=409, detail="El laboratorio está dado de baja")

    repetido = session.exec(
        select(Producto).where(
            func.lower(Producto.nombre) == final["nombre"].lower(),
            Producto.laboratorio_id == final["laboratorio_id"],
            Producto.id_producto != id_producto,
        )
    ).first()
    if repetido:
        raise HTTPException(status_code=409, detail="Ya existe un producto con ese nombre y laboratorio")

    for campo, valor in cambios.items():
        setattr(producto, campo, Decimal(str(valor)) if campo == "precio" else valor)
    session.add(producto)
    session.commit()
    session.refresh(producto)
    return _con_stock(session, producto)


# Baja lógica: el producto deja de listarse pero se conserva su historial.
@router.patch("/{id_producto}/baja", response_model=ProductoRespuesta)
def dar_de_baja_producto(
    id_producto: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_EDICION_PRODUCTO)),
):
    producto = _buscar_producto(session, id_producto)
    producto.activo = False
    session.add(producto)
    session.commit()
    session.refresh(producto)
    return _con_stock(session, producto)


@router.patch("/{id_producto}/reactivar", response_model=ProductoRespuesta)
def reactivar_producto(
    id_producto: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_EDICION_PRODUCTO)),
):
    producto = _buscar_producto(session, id_producto)
    producto.activo = True
    session.add(producto)
    session.commit()
    session.refresh(producto)
    return _con_stock(session, producto)
