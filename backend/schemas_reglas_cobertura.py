from decimal import Decimal

from pydantic import BaseModel, Field


class ReglaCoberturaGuardar(BaseModel):
    # De 0 a 100, con hasta dos decimales (lo que admite la columna de la base).
    porcentaje_cobertura: Decimal = Field(ge=0, le=100, decimal_places=2)


class ReglaCoberturaRespuesta(BaseModel):
    id_regla_cobertura: int
    obra_social_id: int
    categoria_cobertura_obra_social_id: int
    categoria: str
    porcentaje_cobertura: float
