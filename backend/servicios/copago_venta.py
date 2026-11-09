from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from sqlmodel import Session, select

from models import CategoriaCoberturaObraSocial, Medicamento, ObraSocial, Producto, ReglaCobertura
from schemas_ventas import LineaVenta
from servicios.base_ventas import ErrorDeVenta, importe, juntar_lineas, producto_vendible
from servicios.copago import LineaACubrir, LineaCubierta, calcular_copago, elegir_estrategia


class ObraSocialNoEncontrada(ErrorDeVenta):
    estado_http = 404


class ObraSocialDadaDeBaja(ErrorDeVenta):
    estado_http = 409


# Un producto del pedido (las líneas repetidas ya están sumadas) con lo que cubre la obra social.
@dataclass
class LineaCalculada:
    producto: Producto
    cantidad: int
    categoria: Optional[str]
    importe: Decimal
    cubierta: LineaCubierta


@dataclass
class CopagoDeVenta:
    obra_social: ObraSocial
    lineas: list[LineaCalculada]
    subtotal: Decimal
    cobertura: Decimal
    total_a_pagar: Decimal  # lo que paga el cliente


def _obra_social_activa(session: Session, id_obra_social: int) -> ObraSocial:
    obra_social = session.get(ObraSocial, id_obra_social)
    if obra_social is None:
        raise ObraSocialNoEncontrada("Obra social no encontrada")
    if not obra_social.activo:
        raise ObraSocialDadaDeBaja(f"La obra social {obra_social.nombre} está dada de baja")
    return obra_social


# Porcentaje de cobertura de la obra social por id de categoría.
def _reglas_de(session: Session, id_obra_social: int) -> dict[int, Decimal]:
    reglas = session.exec(
        select(ReglaCobertura).where(ReglaCobertura.obra_social_id == id_obra_social, ReglaCobertura.activo.is_(True))
    ).all()
    return {r.categoria_cobertura_obra_social_id: r.porcentaje_cobertura for r in reglas}


# Solo los medicamentos tienen categoría de cobertura; el resto de los productos se paga completo.
def _categoria_del_producto(session: Session, id_producto: int) -> tuple[Optional[int], Optional[str]]:
    medicamento = session.get(Medicamento, id_producto)
    if medicamento is None or medicamento.categoria_cobertura_obra_social_id is None:
        return None, None
    categoria = session.get(CategoriaCoberturaObraSocial, medicamento.categoria_cobertura_obra_social_id)
    return categoria.id_categoria_cobertura_obra_social, categoria.nombre


# Calcula cuánto cubre la obra social y cuánto paga el cliente, sin guardar nada.
# No mira el stock: eso lo controla el registro de la venta.
def calcular_copago_de_venta(session: Session, id_obra_social: int, lineas: list[LineaVenta]) -> CopagoDeVenta:
    obra_social = _obra_social_activa(session, id_obra_social)

    productos = []
    for id_producto, cantidad in juntar_lineas(lineas).items():
        producto = producto_vendible(session, id_producto)
        id_categoria, categoria = _categoria_del_producto(session, id_producto)
        productos.append((producto, cantidad, id_categoria, categoria, importe(producto.precio, cantidad)))

    estrategia = elegir_estrategia(obra_social.tipo_validacion, _reglas_de(session, id_obra_social))
    resultado = calcular_copago([LineaACubrir(imp, id_cat) for _, _, id_cat, _, imp in productos], estrategia)

    calculadas = [
        LineaCalculada(producto, cantidad, categoria, imp, cubierta)
        for (producto, cantidad, _, categoria, imp), cubierta in zip(productos, resultado.lineas)
    ]
    return CopagoDeVenta(
        obra_social=obra_social,
        lineas=calculadas,
        subtotal=sum((c.importe for c in calculadas), Decimal("0")),
        cobertura=resultado.cobertura,
        total_a_pagar=resultado.copago,
    )
