from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    nombre_usuario: str
    contrasena: str


class LoginResponse(BaseModel):
    token: str
    nombre: str
    rol: str
    debe_cambiar_contrasena: bool = False


class CambiarContrasenaPropia(BaseModel):
    contrasena_actual: str
    contrasena_nueva: str = Field(min_length=8)
