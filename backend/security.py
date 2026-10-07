import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITMO = "HS256"
MINUTOS_DE_VIDA = 60

password_hash = PasswordHash.recommended()


def hashear_contrasena(contrasena: str) -> str:
    return password_hash.hash(contrasena)


def verificar_contrasena(contrasena: str, contrasena_hash: str) -> bool:
    return password_hash.verify(contrasena, contrasena_hash)


def crear_token(nombre_usuario: str, rol: str, debe_cambiar: bool = False) -> str:
    vencimiento = datetime.now(timezone.utc) + timedelta(minutes=MINUTOS_DE_VIDA)
    datos = {"sub": nombre_usuario, "rol": rol, "cambiar": debe_cambiar, "exp": vencimiento}
    return jwt.encode(datos, SECRET_KEY, algorithm=ALGORITMO)


def leer_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO])

