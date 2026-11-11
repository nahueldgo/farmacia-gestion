from pydantic import AliasChoices, BaseModel, Field, computed_field


# Unificación de los nombres del login a snake_case (docs/04, "Convenciones de la API"):
# mientras el frontend no pase a los nombres nuevos, se aceptan y se devuelven los dos.
class LoginRequest(BaseModel):
    nombre_usuario: str = Field(validation_alias=AliasChoices("nombre_usuario", "nombreUsuario"))
    contrasena: str


class LoginResponse(BaseModel):
    token: str
    nombre: str
    rol: str
    debe_cambiar_contrasena: bool = False

    # Nombre anterior: se elimina junto con el alias de arriba cuando el frontend ya use el nuevo.
    @computed_field
    @property
    def debeCambiarContrasena(self) -> bool:
        return self.debe_cambiar_contrasena


class CambiarContrasenaPropia(BaseModel):
    contrasena_actual: str
    contrasena_nueva: str = Field(min_length=8)
