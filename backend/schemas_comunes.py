from pydantic import BaseModel, ConfigDict


# Base de los pedidos con texto: recorta los espacios de los extremos antes de validar.
class DatosRecortados(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


# Para los textos opcionales: en blanco es lo mismo que no mandarlos.
def en_blanco_es_nada(valor):
    if isinstance(valor, str) and not valor.strip():
        return None
    return valor
