from pydantic import BaseModel


class CondicionIvaRespuesta(BaseModel):
    id_condicion_iva: int
    nombre: str
    alicuota: float

class CatalogoCrear(BaseModel):
    nombre: str
    
    