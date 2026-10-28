from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func

from comun import buscar_producto, nombre_limpio, obtener_o_404
from db import get_session
from dependencias import obtener_usuario_actual, requiere_rol
from fechas import hoy
from models import Producto, Laboratorio, CondicionIva, Medicamento, Lote
from roles import ROLES_OPERATIVOS, SOLO_FARMACEUTICO
from schemas_productos import ProductoCrear, ProductoEditar, ProductoRespuesta, TipoProducto


router = APIRouter(prefix="/productos", tags=["productos"])

ROLES_ALTA_PRODUCTO = ROLES_OPERATIVOS
ROLES_EDICION_PRODUCTO = SOLO_FARMACEUTICO


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


# Las tres comprobaciones siguientes las comparten el alta y la edición.
def _controlar_tipo_y_laboratorio(tipo: str, laboratorio_id: Optional[int]) -> None:
    if tipo == TipoProducto.MEDICAMENTO and laboratorio_id is None:
        raise HTTPException(status_code=422, detail="Un medicamento necesita laboratorio")


# Solo se revisan los ids que se mandan: tienen que existir, y el laboratorio estar activo.
def _controlar_referencias(
    session: Session, condicion_iva_id: Optional[int] = None, laboratorio_id: Optional[int] = None
) -> None:
    if condicion_iva_id is not None:
        obtener_o_404(session, CondicionIva, condicion_iva_id, "No existe esa condición de IVA")
    if laboratorio_id is not None:
        laboratorio = obtener_o_404(session, Laboratorio, laboratorio_id, "No existe ese laboratorio")
        if not laboratorio.activo:
            raise HTTPException(status_code=409, detail="El laboratorio está dado de baja")


# No puede haber dos productos con el mismo nombre y laboratorio; id_propio excluye al que se edita.
def _verificar_producto_libre(
    session: Session, nombre: str, laboratorio_id: Optional[int], id_propio: Optional[int] = None
) -> None:
    consulta = select(Producto).where(
        func.lower(Producto.nombre) == nombre.lower(),
        Producto.laboratorio_id == laboratorio_id,
    )
    if id_propio is not None:
        consulta = consulta.where(Producto.id_producto != id_propio)
    if session.exec(consulta).first():
        raise HTTPException(status_code=409, detail="Ya existe un producto con ese nombre y laboratorio")


@router.post("", response_model=ProductoRespuesta, status_code=201)
def crear_producto(
    datos: ProductoCrear,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_ALTA_PRODUCTO)),
):
    nombre = nombre_limpio(datos.nombre)
    _controlar_tipo_y_laboratorio(datos.tipo_producto, datos.laboratorio_id)
    _controlar_referencias(session, datos.condicion_iva_id, datos.laboratorio_id)
    _verificar_producto_libre(session, nombre, datos.laboratorio_id)

    producto = Producto(
        nombre=nombre,
        descripcion=datos.descripcion,
        laboratorio_id=datos.laboratorio_id,
        precio=Decimal(str(datos.precio)),
        condicion_iva_id=datos.condicion_iva_id,
        tipo_producto=datos.tipo_producto.value,
        stock_minimo=datos.stock_minimo,
    )
    session.add(producto)
    session.commit()
    session.refresh(producto)
    return _con_stock(session, producto)


@router.get("", response_model=list[ProductoRespuesta])
def listar_productos(
    buscar: Optional[str] = None,
    incluir_inactivos: bool = False,
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    # Ver también los dados de baja es solo del farmacéutico: los necesita para reactivarlos.
    if incluir_inactivos and usuario.get("rol") not in ROLES_EDICION_PRODUCTO:
        raise HTTPException(status_code=403, detail="Solo el farmacéutico puede ver los productos dados de baja")
    consulta = select(Producto)
    if not incluir_inactivos:
        consulta = consulta.where(Producto.activo.is_(True))
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
    return _con_stock(session, buscar_producto(session, id_producto))


@router.patch("/{id_producto}", response_model=ProductoRespuesta)
def editar_producto(
    id_producto: int,
    datos: ProductoEditar,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_EDICION_PRODUCTO)),
):
    producto = buscar_producto(session, id_producto)
    # Solo los campos que vinieron en el pedido.
    cambios = datos.model_dump(exclude_unset=True)

    for campo in ("nombre", "precio", "condicion_iva_id", "tipo_producto", "stock_minimo"):
        if campo in cambios and cambios[campo] is None:
            raise HTTPException(status_code=422, detail=f"El campo {campo} no puede ser nulo")
    if "nombre" in cambios:
        cambios["nombre"] = nombre_limpio(cambios["nombre"])

    # Cómo quedaría el producto, para validar las reglas sobre el resultado final.
    final = {
        "nombre": producto.nombre,
        "laboratorio_id": producto.laboratorio_id,
        "tipo_producto": producto.tipo_producto,
        **cambios,
    }
    _controlar_tipo_y_laboratorio(final["tipo_producto"], final["laboratorio_id"])
    if final["tipo_producto"] != TipoProducto.MEDICAMENTO and session.get(Medicamento, id_producto) is not None:
        raise HTTPException(status_code=409, detail="El producto tiene datos de medicamento: no puede cambiar de tipo")
    _controlar_referencias(session, cambios.get("condicion_iva_id"), cambios.get("laboratorio_id"))
    _verificar_producto_libre(session, final["nombre"], final["laboratorio_id"], id_propio=id_producto)

    for campo, valor in cambios.items():
        if campo == "precio":
            valor = Decimal(str(valor))
        elif campo == "tipo_producto":
            valor = valor.value
        setattr(producto, campo, valor)
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
    producto = buscar_producto(session, id_producto)
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
    producto = buscar_producto(session, id_producto)
    producto.activo = True
    session.add(producto)
    session.commit()
    session.refresh(producto)
    return _con_stock(session, producto)
