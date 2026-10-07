from typing import Optional

from pydantic import BaseModel


class MedicamentoCrear(BaseModel):
    principio_activo_id: int
    concentracion: str
    forma_farmaceutica_id: int
    requiere_receta: bool = False
    categoria_cobertura_obra_social_id: Optional[int] = None
    clases_terapeuticas_ids: list[int] = []


class MedicamentoEditar(BaseModel):
    principio_activo_id: Optional[int] = None
    concentracion: Optional[str] = None
    forma_farmaceutica_id: Optional[int] = None
    requiere_receta: Optional[bool] = None
    categoria_cobertura_obra_social_id: Optional[int] = None
    clases_terapeuticas_ids: Optional[list[int]] = None


class MedicamentoRespuesta(BaseModel):
    producto_id: int
    principio_activo_id: int
    concentracion: str
    forma_farmaceutica_id: int
    requiere_receta: bool
    categoria_cobertura_obra_social_id: Optional[int]
    clases_terapeuticas_ids: list[int]
