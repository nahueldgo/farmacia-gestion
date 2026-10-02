from datetime import date, datetime
from typing import Optional
from decimal import Decimal


from sqlmodel import Field, SQLModel

class Empleado(SQLModel, table=True):
    __tablename__ = "empleado"

    id_empleado: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    apellido: str
    dni: str
    rol: str
    matricula_profesional: Optional[str] = None
    fecha_ingreso: date
    activo: bool = True

class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"

    id_usuario: Optional[int] = Field(default=None, primary_key=True)
    empleado_id: int = Field(foreign_key="empleado.id_empleado", unique=True)
    nombre_usuario: str = Field(unique=True)
    email: str = Field(unique=True)
    contrasena_hash: str
    activo: bool = True
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    ultimo_login: Optional[datetime] = None


class CategoriaCoberturaObraSocial(SQLModel, table=True):
    __tablename__ = "categoria_cobertura_obra_social"

    id_categoria_cobertura_obra_social: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)

class Laboratorio(SQLModel, table=True):
    __tablename__ = "laboratorio"

    id_laboratorio: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)
    activo: bool = True


class PrincipioActivo(SQLModel, table=True):
    __tablename__ = "principio_activo"

    id_principio_activo: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)


class CondicionIva(SQLModel, table=True):
    __tablename__ = "condicion_iva"

    id_condicion_iva: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)
    alicuota: Decimal


class FormaFarmaceutica(SQLModel, table=True):
    __tablename__ = "forma_farmaceutica"

    id_forma_farmaceutica: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)


class ClaseTerapeutica(SQLModel, table=True):
    __tablename__ = "clase_terapeutica"

    id_clase_terapeutica: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)


class Producto(SQLModel, table=True):
    __tablename__ = "producto"

    id_producto: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    descripcion: Optional[str] = None
    laboratorio_id: Optional[int] = Field(default=None, foreign_key="laboratorio.id_laboratorio")
    precio: Decimal
    condicion_iva_id: int = Field(foreign_key="condicion_iva.id_condicion_iva")
    tipo_producto: str
    stock_minimo: int = 0
    activo: bool = True


class Medicamento(SQLModel, table=True):
    __tablename__ = "medicamento"

    producto_id: int = Field(primary_key=True, foreign_key="producto.id_producto")
    principio_activo_id: int = Field(foreign_key="principio_activo.id_principio_activo")
    concentracion: str
    forma_farmaceutica_id: int = Field(foreign_key="forma_farmaceutica.id_forma_farmaceutica")
    requiere_receta: bool = False
    categoria_cobertura_obra_social_id: Optional[int] = Field(
        default=None, foreign_key="categoria_cobertura_obra_social.id_categoria_cobertura_obra_social"
    )


class MedicamentoClaseTerapeutica(SQLModel, table=True):
    __tablename__ = "medicamento_clase_terapeutica"

    medicamento_id: int = Field(primary_key=True, foreign_key="medicamento.producto_id")
    clase_terapeutica_id: int = Field(primary_key=True, foreign_key="clase_terapeutica.id_clase_terapeutica")


class Lote(SQLModel, table=True):
    __tablename__ = "lote"

    id_lote: Optional[int] = Field(default=None, primary_key=True)
    producto_id: int = Field(foreign_key="producto.id_producto")
    numero_lote: str
    fecha_vencimiento: date
    cantidad: int
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)