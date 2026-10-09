from sqlmodel import Session, select

from fechas import hoy
from models import Lote


class StockInsuficiente(Exception):
    def __init__(self, pedido: int, disponible: int):
        self.pedido = pedido
        self.disponible = disponible
        super().__init__(f"Stock insuficiente: se pidieron {pedido} y hay {disponible}")


# FEFO: elige los lotes que vencen antes; ignora los vencidos y los agotados.
# Devuelve una lista de (lote, cantidad que se toma de ese lote). No modifica nada.
def elegir_lotes(
    session: Session, id_producto: int, cantidad: int, bloquear: bool = False
) -> list[tuple[Lote, int]]:
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor a 0")

    consulta = (
        select(Lote)
        .where(
            Lote.producto_id == id_producto,
            Lote.cantidad > 0,
            Lote.fecha_vencimiento >= hoy(),
        )
        .order_by(Lote.fecha_vencimiento, Lote.id_lote)
    )
    if bloquear:
        consulta = consulta.with_for_update()  # evita que dos ventas usen el mismo stock a la vez

    elegidos = []
    faltan = cantidad
    for lote in session.exec(consulta).all():
        if faltan == 0:
            break
        tomar = min(lote.cantidad, faltan)
        elegidos.append((lote, tomar))
        faltan -= tomar

    if faltan > 0:
        raise StockInsuficiente(pedido=cantidad, disponible=cantidad - faltan)
    return elegidos


# Descuenta por FEFO dentro de la transacción de quien la llama (la venta). No hace commit.
# Devuelve (id_lote, cantidad) por cada lote usado, para guardarlo en el detalle de la venta.
def descontar_stock(session: Session, id_producto: int, cantidad: int) -> list[tuple[int, int]]:
    elegidos = elegir_lotes(session, id_producto, cantidad, bloquear=True)
    usados = []
    for lote, tomar in elegidos:
        lote.cantidad -= tomar
        session.add(lote)
        usados.append((lote.id_lote, tomar))
    return usados
