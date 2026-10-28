from fastapi import HTTPException
from sqlmodel import Session, func, select

from models import Producto, Usuario


# Busca por clave primaria; si no existe, responde 404 con el mensaje dado.
def obtener_o_404(session: Session, modelo, id_objeto: int, mensaje: str):
    objeto = session.get(modelo, id_objeto)
    if objeto is None:
        raise HTTPException(status_code=404, detail=mensaje)
    return objeto


def buscar_producto(session: Session, id_producto: int) -> Producto:
    return obtener_o_404(session, Producto, id_producto, "Producto no encontrado")


# Recorta el nombre y rechaza el vacío.
def nombre_limpio(nombre: str) -> str:
    nombre = nombre.strip()
    if not nombre:
        raise HTTPException(status_code=422, detail="El nombre no puede estar vacío")
    return nombre


# Rechaza el nombre si ya lo tiene otro registro, sin distinguir mayúsculas; id_propio excluye al registro que se edita.
def verificar_nombre_libre(session: Session, modelo, columna_id, nombre: str, mensaje: str, id_propio: int | None = None) -> None:
    consulta = select(modelo).where(func.lower(modelo.nombre) == nombre.lower())
    if id_propio is not None:
        consulta = consulta.where(columna_id != id_propio)
    if session.exec(consulta).first():
        raise HTTPException(status_code=409, detail=mensaje)


# Busca un usuario por su nombre de usuario; devuelve None si no existe.
def buscar_usuario(session: Session, nombre_usuario: str) -> Usuario | None:
    return session.exec(select(Usuario).where(Usuario.nombre_usuario == nombre_usuario)).first()


# El usuario que hizo el pedido, según su token; si ya no existe, responde 401.
def usuario_del_token(session: Session, usuario: dict) -> Usuario:
    fila = buscar_usuario(session, usuario["sub"])
    if fila is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return fila


# El empleado sale del token, no lo manda el cliente.
def empleado_del_usuario(session: Session, usuario: dict) -> int:
    return usuario_del_token(session, usuario).empleado_id
