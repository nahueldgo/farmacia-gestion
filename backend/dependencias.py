from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from security import leer_token

seguridad_bearer = HTTPBearer(auto_error=False)


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(seguridad_bearer),
) -> dict:
    if credenciales is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    token = credenciales.credentials
    try:
        return leer_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token vencido")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


def requiere_rol(*roles_permitidos: str):
    def verificar_rol(usuario: dict = Depends(obtener_usuario_actual)) -> dict:
        if usuario.get("rol") not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenés permiso para acceder a este recurso",
            )
        return usuario

    return verificar_rol
