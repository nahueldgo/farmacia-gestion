from datetime import date
from getpass import getpass

from sqlmodel import Session, select

from db import engine
from models import Empleado, Usuario
from roles import Rol
from security import hashear_contrasena


def pedir(texto: str) -> str:
    valor = input(texto + ": ").strip()
    if not valor:
        raise SystemExit("El dato no puede quedar vacío.")
    return valor


# Crea el primer dueño real. Se corre una sola vez, a mano.
def crear_dueno():
    with Session(engine) as session:
        hay_dueno = session.exec(
            select(Empleado).where(Empleado.rol == Rol.DUENO.value, Empleado.activo.is_(True))
        ).first()
        if hay_dueno and input("Ya hay un dueño activo. ¿Crear otro igual? (s/n): ").strip().lower() != "s":
            raise SystemExit("No se creó nada.")

        nombre = pedir("Nombre")
        apellido = pedir("Apellido")
        dni = pedir("DNI")
        nombre_usuario = pedir("Nombre de usuario")
        email = pedir("Email")
        contrasena = getpass("Contraseña (mínimo 8 caracteres): ")
        if len(contrasena) < 8:
            raise SystemExit("La contraseña debe tener al menos 8 caracteres.")
        if contrasena != getpass("Repetí la contraseña: "):
            raise SystemExit("Las contraseñas no coinciden.")

        if session.exec(select(Empleado).where(Empleado.dni == dni)).first():
            raise SystemExit("Ya existe un empleado con ese DNI.")
        if session.exec(select(Usuario).where(Usuario.nombre_usuario == nombre_usuario)).first():
            raise SystemExit("Ya existe un usuario con ese nombre de usuario.")
        if session.exec(select(Usuario).where(Usuario.email == email)).first():
            raise SystemExit("Ya existe un usuario con ese email.")

        empleado = Empleado(
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            rol=Rol.DUENO.value,
            fecha_ingreso=date.today(),
        )
        session.add(empleado)
        session.flush()  # asigna id_empleado sin cerrar la transacción

        session.add(Usuario(
            empleado_id=empleado.id_empleado,
            nombre_usuario=nombre_usuario,
            email=email,
            contrasena_hash=hashear_contrasena(contrasena),
        ))
        session.commit()
        print("Dueño creado:", nombre_usuario)


if __name__ == "__main__":
    crear_dueno()
    