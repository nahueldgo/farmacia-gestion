from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from comun import CLIENTE_NO_ENCONTRADO
from fechas import ahora_utc, hoy, rango_utc_del_dia
from fefo import StockInsuficiente, descontar_stock
from models import Caja, Cliente, CondicionIva, DetalleVenta, Empleado, Producto, Venta
from schemas_ventas import EstadoVenta, LineaVenta, VentaCrear
from servicios.base_ventas import ErrorDeVenta, importe, juntar_lineas, producto_vendible
from servicios.copago_venta import CopagoDeVenta, calcular_copago_de_venta


class SinCajaAbierta(ErrorDeVenta):
    estado_http = 409


class ClienteNoEncontrado(ErrorDeVenta):
    estado_http = 404


class StockInsuficienteDe(ErrorDeVenta):
    estado_http = 409


class RangoDeFechasInvalido(ErrorDeVenta):
    estado_http = 422


class VentaYaAnulada(ErrorDeVenta):
    estado_http = 409


# Lo que la venta toma de un lote de un producto.
@dataclass
class Tramo:
    producto: Producto
    alicuota: Decimal
    id_lote: int
    cantidad: int


@dataclass
class Montos:
    subtotal: Decimal
    gravado: Decimal
    exento: Decimal
    total: Decimal


def formatear_comprobante(numero: int) -> str:
    return f"V-{numero:08d}"


# Cada parte es (precio con IVA incluido, alícuota, cantidad). El IVA va incluido en el precio.
def calcular_montos(partes: list[tuple[Decimal, Decimal, int]]) -> Montos:
    subtotal = gravado = exento = Decimal("0")
    for precio, alicuota, cantidad in partes:
        monto = importe(precio, cantidad)
        subtotal += monto
        if alicuota > 0:
            gravado += monto
        else:
            exento += monto
    return Montos(subtotal=subtotal, gravado=gravado, exento=exento, total=subtotal)


# Si el pedido trae una clave que ya se registró, devuelve esa venta.
def _venta_ya_registrada(session: Session, clave: Optional[str]) -> Optional[Venta]:
    if clave is None:
        return None
    return session.exec(select(Venta).where(Venta.clave_operacion == clave)).first()


def _caja_abierta(session: Session) -> Caja:
    caja = session.exec(select(Caja).where(Caja.estado == "abierta")).first()
    if caja is None:
        raise SinCajaAbierta("No hay una caja abierta: abrila antes de vender")
    return caja


# Descuenta el stock de cada producto por FEFO y devuelve de qué lotes salió.
def _descontar_lineas(session: Session, lineas: list[LineaVenta]) -> list[Tramo]:
    tramos = []
    for id_producto, cantidad in juntar_lineas(lineas).items():
        producto = producto_vendible(session, id_producto)
        alicuota = session.get(CondicionIva, producto.condicion_iva_id).alicuota
        try:
            usados = descontar_stock(session, id_producto, cantidad)
        except StockInsuficiente as error:
            raise StockInsuficienteDe(
                f"Stock insuficiente de {producto.nombre}: se pidieron {error.pedido} y hay {error.disponible}"
            )
        tramos += [Tramo(producto, alicuota, id_lote, tomado) for id_lote, tomado in usados]
    return tramos


def _proximo_comprobante(session: Session) -> str:
    numero = session.execute(text("SELECT nextval('seq_numero_comprobante')")).scalar_one()
    return formatear_comprobante(numero)


# En la venta con obra social, el cliente tiene que existir y la cobertura se calcula igual que en el cálculo previo.
def _copago_del_pedido(session: Session, datos: VentaCrear) -> Optional[CopagoDeVenta]:
    if datos.obra_social_id is None:
        return None
    if session.get(Cliente, datos.cliente_id) is None:
        raise ClienteNoEncontrado(CLIENTE_NO_ENCONTRADO)
    return calcular_copago_de_venta(session, datos.obra_social_id, datos.lineas)


# Agrega la venta y su detalle a la transacción; no hace commit.
# El gravado y el exento salen del precio de lista; la cobertura solo baja lo que paga el cliente.
def _agregar_venta(
    session: Session, caja: Caja, id_empleado: int, datos: VentaCrear, tramos: list[Tramo], copago: Optional[CopagoDeVenta]
) -> Venta:
    montos = calcular_montos([(t.producto.precio, t.alicuota, t.cantidad) for t in tramos])
    venta = Venta(
        numero_comprobante=_proximo_comprobante(session),
        clave_operacion=datos.clave_operacion,
        empleado_id=id_empleado,
        cliente_id=datos.cliente_id,
        obra_social_id=datos.obra_social_id,
        caja_id=caja.id_caja,
        medio_pago=datos.medio_pago.value,
        subtotal=montos.subtotal,
        monto_cobertura=copago.cobertura if copago else Decimal("0"),
        monto_gravado=montos.gravado,
        monto_exento=montos.exento,
        total_a_pagar=copago.total_a_pagar if copago else montos.total,
        receta_verificada=datos.receta_verificada,
    )
    session.add(venta)
    session.flush()  # para conocer el id de la venta antes de guardar su detalle
    for tramo in tramos:
        session.add(
            DetalleVenta(
                venta_id=venta.id_venta,
                producto_id=tramo.producto.id_producto,
                lote_id=tramo.id_lote,
                cantidad=tramo.cantidad,
                precio_unitario=tramo.producto.precio,
                subtotal=importe(tramo.producto.precio, tramo.cantidad),
            )
        )
    return venta


# Registra la venta en una sola transacción: la venta, su detalle, la cobertura y el descuento de stock.
# Devuelve (venta, creada): creada es False si ese pedido ya estaba registrado.
def crear_venta(session: Session, id_empleado: int, datos: VentaCrear) -> tuple[Venta, bool]:
    existente = _venta_ya_registrada(session, datos.clave_operacion)
    if existente:
        return existente, False

    caja = _caja_abierta(session)
    copago = _copago_del_pedido(session, datos)
    try:
        tramos = _descontar_lineas(session, datos.lineas)
        venta = _agregar_venta(session, caja, id_empleado, datos, tramos, copago)
        session.commit()
    except IntegrityError:
        session.rollback()
        # El mismo pedido llegó dos veces a la vez: la base rechazó la segunda clave.
        existente = _venta_ya_registrada(session, datos.clave_operacion)
        if existente is None:
            raise
        return existente, False
    except Exception:
        session.rollback()
        raise

    session.refresh(venta)
    return venta, True


# Sin fechas, las de hoy. Con una sola, ese día. Con las dos, todos los días entre ellas.
def resolver_periodo(desde: Optional[date], hasta: Optional[date], dia_actual: date) -> tuple[date, date]:
    primer_dia = desde or hasta or dia_actual
    ultimo_dia = hasta or primer_dia
    if ultimo_dia < primer_dia:
        raise RangoDeFechasInvalido("La fecha hasta no puede ser anterior a la fecha desde")
    return primer_dia, ultimo_dia


# Las ventas de un período (días de Argentina), de la más reciente a la más antigua, con quien las hizo.
def ventas_del_periodo(
    session: Session, desde: Optional[date], hasta: Optional[date], estado: Optional[EstadoVenta]
) -> list[tuple[Venta, Empleado]]:
    primer_dia, ultimo_dia = resolver_periodo(desde, hasta, hoy())
    inicio, _ = rango_utc_del_dia(primer_dia)
    _, fin = rango_utc_del_dia(ultimo_dia)
    consulta = (
        select(Venta, Empleado)
        .where(Venta.empleado_id == Empleado.id_empleado, Venta.fecha >= inicio, Venta.fecha < fin)
        .order_by(Venta.fecha.desc(), Venta.id_venta.desc())
    )
    if estado:
        consulta = consulta.where(Venta.estado == estado.value)
    return session.exec(consulta).all()


# La venta no se borra: pasa a "anulada" y queda quién la anuló y cuándo. El stock no se reintegra.
def anular_venta(session: Session, venta: Venta, id_empleado: int) -> Venta:
    session.refresh(venta, with_for_update=True)  # bloquea la fila: dos anulaciones a la vez no se pisan
    if venta.estado == EstadoVenta.ANULADA.value:
        session.rollback()
        raise VentaYaAnulada("La venta ya está anulada")
    venta.estado = EstadoVenta.ANULADA.value
    venta.empleado_anulacion_id = id_empleado
    venta.fecha_anulacion = ahora_utc()
    session.add(venta)
    session.commit()
    session.refresh(venta)
    return venta
