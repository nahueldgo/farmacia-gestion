from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    nombreUsuario: str
    contrasena: str


class LoginResponse(BaseModel):
    token: str
    nombre: str
    rol: str
    debeCambiarContrasena: bool = False


class CambiarContrasenaPropia(BaseModel):
    contrasena_actual: str
    contrasena_nueva: str = Field(min_length=8)
