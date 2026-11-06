from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from comun import guardar_o_409, obtener_o_404
from db import get_session
from dependencias import obtener_usuario_actual, requiere_rol
from models import CategoriaCoberturaObraSocial, ObraSocial, ReglaCobertura
from roles import SOLO_FARMACEUTICO
from schemas_reglas_cobertura import ReglaCoberturaGuardar, ReglaCoberturaRespuesta

router = APIRouter(prefix="/obras-sociales/{id_obra_social}/reglas", tags=["reglas de cobertura"])

CATEGORIA = CategoriaCoberturaObraSocial


def _respuesta(regla: ReglaCobertura, categoria: str) -> ReglaCoberturaRespuesta:
    return ReglaCoberturaRespuesta(
        id_regla_cobertura=regla.id_regla_cobertura,
        obra_social_id=regla.obra_social_id,
        categoria_cobertura_obra_social_id=regla.categoria_cobertura_obra_social_id,
        categoria=categoria,
        porcentaje_cobertura=float(regla.porcentaje_cobertura),
    )


# Las categorías que no figuran en la lista no tienen regla: esa obra social no cubre nada de ellas.
@router.get("", response_model=list[ReglaCoberturaRespuesta])
def listar_reglas(
    id_obra_social: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    obtener_o_404(session, ObraSocial, id_obra_social, "Obra social no encontrada")
    filas = session.exec(
        select(ReglaCobertura, CATEGORIA.nombre)
        .join(CATEGORIA, CATEGORIA.id_categoria_cobertura_obra_social == ReglaCobertura.categoria_cobertura_obra_social_id)
        .where(ReglaCobertura.obra_social_id == id_obra_social)
        .order_by(ReglaCobertura.categoria_cobertura_obra_social_id)
    ).all()
    return [_respuesta(regla, categoria) for regla, categoria in filas]


# Crea la regla si no existía o cambia su porcentaje; una regla en 0 equivale a no tener regla.
@router.put("/{id_categoria}", response_model=ReglaCoberturaRespuesta)
def guardar_regla(
    id_obra_social: int,
    id_categoria: int,
    datos: ReglaCoberturaGuardar,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*SOLO_FARMACEUTICO)),
):
    obtener_o_404(session, ObraSocial, id_obra_social, "Obra social no encontrada")
    categoria = obtener_o_404(session, CATEGORIA, id_categoria, "Categoría de cobertura no encontrada")
    regla = session.exec(
        select(ReglaCobertura).where(
            ReglaCobertura.obra_social_id == id_obra_social,
            ReglaCobertura.categoria_cobertura_obra_social_id == id_categoria,
        )
    ).first()
    if regla is None:
        regla = ReglaCobertura(obra_social_id=id_obra_social, categoria_cobertura_obra_social_id=id_categoria)
    regla.porcentaje_cobertura = datos.porcentaje_cobertura
    # Solo falla si otro pedido creó la misma regla en el mismo instante.
    regla = guardar_o_409(session, regla, "Otro pedido guardó esa regla a la vez: volvé a pedir las reglas")
    return _respuesta(regla, categoria.nombre)
