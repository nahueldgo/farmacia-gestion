from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from comun import guardar_o_409, obtener_o_404, verificar_nombre_libre
from db import get_session
from dependencias import obtener_usuario_actual, requiere_rol
from models import ObraSocial
from roles import SOLO_FARMACEUTICO
from schemas_obras_sociales import ObraSocialCrear, ObraSocialEditar, ObraSocialRespuesta

router = APIRouter(prefix="/obras-sociales", tags=["obras sociales"])

# Las configura solo el farmacéutico; los tres roles las consultan.
ROLES_CONFIGURAN = SOLO_FARMACEUTICO


def _buscar_obra_social(session: Session, id_obra_social: int) -> ObraSocial:
    return obtener_o_404(session, ObraSocial, id_obra_social, "Obra social no encontrada")


# El CUIT es el único dato que la base exige distinto.
def _guardar(session: Session, obra_social: ObraSocial) -> ObraSocial:
    return guardar_o_409(session, obra_social, "Ya existe una obra social con ese CUIT")


def _cambiar_activo(session: Session, id_obra_social: int, activo: bool) -> ObraSocial:
    obra_social = _buscar_obra_social(session, id_obra_social)
    obra_social.activo = activo
    return _guardar(session, obra_social)


@router.get("", response_model=list[ObraSocialRespuesta])
def listar_obras_sociales(
    incluir_inactivas: bool = False,
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    # Ver también las dadas de baja es solo del farmacéutico: las necesita para reactivarlas.
    if incluir_inactivas and usuario.get("rol") not in ROLES_CONFIGURAN:
        raise HTTPException(status_code=403, detail="Solo el farmacéutico puede ver las obras sociales dadas de baja")
    consulta = select(ObraSocial)
    if not incluir_inactivas:
        consulta = consulta.where(ObraSocial.activo.is_(True))
    return session.exec(consulta.order_by(ObraSocial.nombre)).all()


@router.get("/{id_obra_social}", response_model=ObraSocialRespuesta)
def consultar_obra_social(
    id_obra_social: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(obtener_usuario_actual),
):
    return _buscar_obra_social(session, id_obra_social)


@router.post("", response_model=ObraSocialRespuesta, status_code=201)
def crear_obra_social(
    datos: ObraSocialCrear,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_CONFIGURAN)),
):
    verificar_nombre_libre(
        session, ObraSocial, ObraSocial.id_obra_social, datos.nombre, "Ya existe una obra social con ese nombre"
    )
    return _guardar(session, ObraSocial(**datos.model_dump(mode="json")))


@router.patch("/{id_obra_social}", response_model=ObraSocialRespuesta)
def editar_obra_social(
    id_obra_social: int,
    datos: ObraSocialEditar,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_CONFIGURAN)),
):
    obra_social = _buscar_obra_social(session, id_obra_social)
    # Solo los campos que vinieron en el pedido; el CUIT y el contacto se pueden vaciar con null.
    cambios = datos.model_dump(exclude_unset=True, mode="json")

    for campo in ("nombre", "tipo_validacion"):
        if campo in cambios and cambios[campo] is None:
            raise HTTPException(status_code=422, detail=f"El campo {campo} no puede ser nulo")
    if "nombre" in cambios:
        verificar_nombre_libre(
            session, ObraSocial, ObraSocial.id_obra_social, cambios["nombre"],
            "Ya existe una obra social con ese nombre", id_propio=id_obra_social,
        )

    for campo, valor in cambios.items():
        setattr(obra_social, campo, valor)
    return _guardar(session, obra_social)


# Baja lógica: deja de ofrecerse al vender, pero conserva sus ventas y sus reglas de cobertura.
@router.patch("/{id_obra_social}/baja", response_model=ObraSocialRespuesta)
def dar_de_baja_obra_social(
    id_obra_social: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_CONFIGURAN)),
):
    return _cambiar_activo(session, id_obra_social, False)


@router.patch("/{id_obra_social}/reactivar", response_model=ObraSocialRespuesta)
def reactivar_obra_social(
    id_obra_social: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(requiere_rol(*ROLES_CONFIGURAN)),
):
    return _cambiar_activo(session, id_obra_social, True)
