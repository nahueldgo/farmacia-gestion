from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from db import get_session
from dependencias import obtener_usuario_actual, requiere_rol
from models import (
    Producto, Medicamento, MedicamentoClaseTerapeutica, PrincipioActivo,
    FormaFarmaceutica, ClaseTerapeutica, CategoriaCoberturaObraSocial,
)
from roles import Rol
from schemas_medicamentos import MedicamentoCrear, MedicamentoEditar, MedicamentoRespuesta

router = APIRouter(prefix="/productos/{id_producto}/medicamento", tags=["medicamentos"])

ROLES_ALTA_MEDICAMENTO = (Rol.FARMACEUTICO, Rol.AUXILIAR)
LARGO_CONCENTRACION = 30
ROLES_EDICION_MEDICAMENTO = (Rol.FARMACEUTICO,)


def _producto_medicamento(session: Session, id_producto: int) -> Producto:
    producto = session.get(Producto, id_producto)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if producto.tipo_producto != "medicamento":
        raise HTTPException(status_code=422, detail="El producto no es un medicamento")
    return producto


def _ids_de_clases(session: Session, id_producto: int) -> list[int]:
    filas = session.exec(
        select(MedicamentoClaseTerapeutica.clase_terapeutica_id)
        .where(MedicamentoClaseTerapeutica.medicamento_id == id_producto)
        .order_by(MedicamentoClaseTerapeutica.clase_terapeutica_id)
    ).all()
    return list(filas)


def _respuesta(session: Session, medicamento: Medicamento) -> MedicamentoRespuesta:
    return MedicamentoRespuesta(
        producto_id=medicamento.producto_id,
        principio_activo_id=medicamento.principio_activo_id,
        concentracion=medicamento.concentracion,
        forma_farmaceutica_id=medicamento.forma_farmaceutica_id,
        requiere_receta=medicamento.requiere_receta,
        categoria_cobertura_obra_social_id=medicamento.categoria_cobertura_obra_social_id,
        clases_terapeuticas_ids=_ids_de_clases(session, medicamento.producto_id),
    )


def _controlar_referencias(session: Session, datos: dict) -> None:
    # Cada id que llegue tiene que existir en su catálogo.
    if "principio_activo_id" in datos and session.get(PrincipioActivo, datos["principio_activo_id"]) is None:
        raise HTTPException(status_code=404, detail="No existe ese principio activo")
    if "forma_farmaceutica_id" in datos and session.get(FormaFarmaceutica, datos["forma_farmaceutica_id"]) is None:
        raise HTTPException(status_code=404, detail="No existe esa forma farmacéutica")
    categoria = datos.get("categoria_cobertura_obra_social_id")
    if categoria is not None and session.get(CategoriaCoberturaObraSocial, categoria) is None:
        raise HTTPException(status_code=404, detail="No existe esa categoría de cobertura")
    for id_clase in datos.get("clases_terapeuticas_ids") or []:
        if session.get(ClaseTerapeutica, id_clase) is None:
            raise HTTPException(status_code=404, detail=f"No existe la clase terapéutica {id_clase}")


def _concentracion_valida(concentracion: str) -> str:
    concentracion = concentracion.strip()
    if not concentracion:
        raise HTTPException(status_code=422, detail="La concentración no puede estar vacía")
    if len(concentracion) > LARGO_CONCENTRACION:
        raise HTTPException(status_code=422, detail=f"La concentración admite hasta {LARGO_CONCENTRACION} caracteres")
    return concentracion


@router.post("", response_model=MedicamentoRespuesta, status_code=201)
def cargar_medicamento(
    id_producto: int,
    datos: MedicamentoCrear,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_ALTA_MEDICAMENTO)),
):
    _producto_medicamento(session, id_producto)
    if session.get(Medicamento, id_producto) is not None:
        raise HTTPException(status_code=409, detail="El producto ya tiene datos de medicamento")

    concentracion = _concentracion_valida(datos.concentracion)
    _controlar_referencias(session, datos.model_dump())

    medicamento = Medicamento(
        producto_id=id_producto,
        principio_activo_id=datos.principio_activo_id,
        concentracion=concentracion,
        forma_farmaceutica_id=datos.forma_farmaceutica_id,
        requiere_receta=datos.requiere_receta,
        categoria_cobertura_obra_social_id=datos.categoria_cobertura_obra_social_id,
    )
    session.add(medicamento)
    session.flush()  # deja la fila lista para que las clases la referencien
    for id_clase in sorted(set(datos.clases_terapeuticas_ids)):
        session.add(MedicamentoClaseTerapeutica(medicamento_id=id_producto, clase_terapeutica_id=id_clase))
    session.commit()
    session.refresh(medicamento)
    return _respuesta(session, medicamento)


@router.get("", response_model=MedicamentoRespuesta)
def consultar_medicamento(
    id_producto: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    _producto_medicamento(session, id_producto)
    medicamento = session.get(Medicamento, id_producto)
    if medicamento is None:
        raise HTTPException(status_code=404, detail="El producto todavía no tiene datos de medicamento")
    return _respuesta(session, medicamento)


@router.patch("", response_model=MedicamentoRespuesta)
def editar_medicamento(
    id_producto: int,
    datos: MedicamentoEditar,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_EDICION_MEDICAMENTO)),
):
    _producto_medicamento(session, id_producto)
    medicamento = session.get(Medicamento, id_producto)
    if medicamento is None:
        raise HTTPException(status_code=404, detail="El producto todavía no tiene datos de medicamento")

    # Solo los campos que vinieron en el pedido.
    cambios = datos.model_dump(exclude_unset=True)

    # Estos campos son obligatorios: no pueden quedar nulos (para vaciar las clases, mandar []).
    for campo in ("principio_activo_id", "concentracion", "forma_farmaceutica_id",
                  "requiere_receta", "clases_terapeuticas_ids"):
        if campo in cambios and cambios[campo] is None:
            raise HTTPException(status_code=422, detail=f"El campo {campo} no puede ser nulo")
    if "concentracion" in cambios:
        cambios["concentracion"] = _concentracion_valida(cambios["concentracion"])
    _controlar_referencias(session, cambios)

    clases = cambios.pop("clases_terapeuticas_ids", None)
    for campo, valor in cambios.items():
        setattr(medicamento, campo, valor)
    session.add(medicamento)

    if clases is not None:
        # Reemplaza la lista completa de clases.
        actuales = session.exec(
            select(MedicamentoClaseTerapeutica).where(MedicamentoClaseTerapeutica.medicamento_id == id_producto)
        ).all()
        for fila in actuales:
            session.delete(fila)
        session.flush()
        for id_clase in sorted(set(clases)):
            session.add(MedicamentoClaseTerapeutica(medicamento_id=id_producto, clase_terapeutica_id=id_clase))

    session.commit()
    session.refresh(medicamento)
    return _respuesta(session, medicamento)
