from datetime import date

from sqlmodel import Session, select

from db import engine
from models import Empleado, Usuario
from security import hashear_contrasena

def cargar_datos_iniciales():
    with Session(engine) as session:
        empleado = session.exec(
            select(Empleado).where(Empleado.dni == "00000000")
        ).first()

        if empleado is None:
            empleado = Empleado(
                nombre="Admin",
                apellido="Prueba",
                dni="00000000",
                rol="farmaceutico",
                fecha_ingreso=date.today(),
            )
            session.add(empleado)
            session.commit()
            session.refresh(empleado)
            print("Empleado creado, id:", empleado.id_empleado)
        else:
            print("Empleado ya existe, id:", empleado.id_empleado)

        usuario = session.exec(
            select(Usuario).where(Usuario.nombre_usuario == "admin")
        ).first()

        if usuario is None:
            usuario = Usuario(
                empleado_id=empleado.id_empleado,
                nombre_usuario="admin",
                email="admin@farmacia.test",
                contrasena_hash=hashear_contrasena("admin1234"),
            )
            session.add(usuario)
            session.commit()
            print("Usuario creado: admin / admin1234")
        else:
            print("Usuario ya existe:", usuario.nombre_usuario)

if __name__ == "__main__":
    cargar_datos_iniciales()
    