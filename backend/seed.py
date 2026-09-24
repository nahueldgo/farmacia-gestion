from datetime import date

from sqlmodel import Session, select

from db import engine
from models import Empleado, Usuario
from security import hashear_contrasena

# Usuarios de prueba, uno por rol. Solo para desarrollo.
USUARIOS_DE_PRUEBA = [
    {
        "nombre": "Admin",
        "apellido": "Prueba",
        "dni": "00000000",
        "rol": "farmaceutico",
        "nombre_usuario": "admin",
        "email": "admin@farmacia.test",
        "contrasena": "admin1234",
    },
    {
        "nombre": "Auxiliar",
        "apellido": "Prueba",
        "dni": "00000001",
        "rol": "auxiliar",
        "nombre_usuario": "auxiliar",
        "email": "auxiliar@farmacia.test",
        "contrasena": "auxiliar1234",
    },
    {
        "nombre": "Dueno",
        "apellido": "Prueba",
        "dni": "00000002",
        "rol": "dueno",
        "nombre_usuario": "dueno",
        "email": "dueno@farmacia.test",
        "contrasena": "dueno1234",
    },
]


def cargar_usuario(session: Session, datos: dict):
    empleado = session.exec(
        select(Empleado).where(Empleado.dni == datos["dni"])
    ).first()

    if empleado is None:
        empleado = Empleado(
            nombre=datos["nombre"],
            apellido=datos["apellido"],
            dni=datos["dni"],
            rol=datos["rol"],
            fecha_ingreso=date.today(),
        )
        session.add(empleado)
        session.commit()
        session.refresh(empleado)
        print("Empleado creado:", datos["nombre_usuario"], "- id:", empleado.id_empleado)
    else:
        print("Empleado ya existe:", datos["nombre_usuario"], "- id:", empleado.id_empleado)

    usuario = session.exec(
        select(Usuario).where(Usuario.nombre_usuario == datos["nombre_usuario"])
    ).first()

    if usuario is None:
        usuario = Usuario(
            empleado_id=empleado.id_empleado,
            nombre_usuario=datos["nombre_usuario"],
            email=datos["email"],
            contrasena_hash=hashear_contrasena(datos["contrasena"]),
        )
        session.add(usuario)
        session.commit()
        print("Usuario creado:", datos["nombre_usuario"], "/", datos["contrasena"], "- rol:", datos["rol"])
    else:
        print("Usuario ya existe:", usuario.nombre_usuario)


def cargar_datos_iniciales():
    with Session(engine) as session:
        for datos in USUARIOS_DE_PRUEBA:
            cargar_usuario(session, datos)


if __name__ == "__main__":
    cargar_datos_iniciales()
    