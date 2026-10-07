from pydantic import BaseModel


class LoginRequest(BaseModel):
    nombreUsuario: str
    contrasena: str


class LoginResponse(BaseModel):
    token: str
    nombre: str
    rol: str
    