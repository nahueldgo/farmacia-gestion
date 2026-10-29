from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from fefo import StockInsuficiente, descontar_stock
from models import Caja, CondicionIva, DetalleVenta, Producto, Venta
from schemas_ventas import LineaVenta, VentaCrear

DOS_DECIMALES = Decimal("0.01")


# Errores de negocio: el router los convierte en la respuesta HTTP que indica cada uno.
class ErrorDeVenta(Exception):
    estado_http = 422

    def __init__(self, mensaje: str):
        self.mensaje = mensaje
        super().__init__(mensaje)


class SinCajaAbierta(ErrorDeVenta):
    estado_http = 409


class ProductoNoEncontrado(ErrorDeVenta):
    estado_http = 404


class ProductoDadoDeBaja(ErrorDeVenta):
    estado_http = 409


class StockInsuficienteDe(ErrorDeVenta):
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


def importe(precio: Decimal, cantidad: int) -> Decimal:
    return (precio * cantidad).quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)


# Si un producto viene en dos líneas, se suman: así se descuenta y se bloquea una sola vez.
def juntar_lineas(lineas: list[LineaVenta]) -> dict[int, int]:
    juntas: dict[int, int] = {}
    for linea in lineas:
        juntas[linea.producto_id] = juntas.get(linea.producto_id, 0) + linea.cantidad
    # Siempre en el mismo orden, para que dos ventas simultáneas no se bloqueen entre sí.
    return dict(sorted(juntas.items()))


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


def _producto_vendible(session: Session, id_producto: int) -> Producto:
    producto = session.get(Producto, id_producto)
    if producto is None:
        raise ProductoNoEncontrado(f"No existe el producto {id_producto}")
    if not producto.activo:
        raise ProductoDadoDeBaja(f"El producto {producto.nombre} está dado de baja")
    return producto


# Descuenta el stock de cada producto por FEFO y devuelve de qué lotes salió.
def _descontar_lineas(session: Session, lineas: list[LineaVenta]) -> list[Tramo]:
    tramos = []
    for id_producto, cantidad in juntar_lineas(lineas).items():
        producto = _producto_vendible(session, id_producto)
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


# Agrega la venta y su detalle a la transacción; no hace commit.
def _agregar_venta(session: Session, caja: Caja, id_empleado: int, datos: VentaCrear, tramos: list[Tramo]) -> Venta:
    montos = calcular_montos([(t.producto.precio, t.alicuota, t.cantidad) for t in tramos])
    venta = Venta(
        numero_comprobante=_proximo_comprobante(session),
        clave_operacion=datos.clave_operacion,
        empleado_id=id_empleado,
        caja_id=caja.id_caja,
        medio_pago=datos.medio_pago.value,
        subtotal=montos.subtotal,
        monto_gravado=montos.gravado,
        monto_exento=montos.exento,
        total_a_pagar=montos.total,
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


# Registra la venta en una sola transacción: la venta, su detalle y el descuento de stock.
# Devuelve (venta, creada): creada es False si ese pedido ya estaba registrado.
def crear_venta(session: Session, id_empleado: int, datos: VentaCrear) -> tuple[Venta, bool]:
    existente = _venta_ya_registrada(session, datos.clave_operacion)
    if existente:
        return existente, False

    caja = _caja_abierta(session)
    try:
        tramos = _descontar_lineas(session, datos.lineas)
        venta = _agregar_venta(session, caja, id_empleado, datos, tramos)
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
