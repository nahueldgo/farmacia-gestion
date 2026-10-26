from datetime import date, datetime
from typing import Optional
from decimal import Decimal


from sqlmodel import Field, SQLModel

from fechas import ahora_utc

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
    debe_cambiar_contrasena: bool = False
    fecha_creacion: datetime = Field(default_factory=ahora_utc)
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
    fecha_creacion: datetime = Field(default_factory=ahora_utc)


class Cliente(SQLModel, table=True):
    __tablename__ = "cliente"

    id_cliente: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    apellido: str
    dni: str = Field(unique=True)
    telefono: Optional[str] = None
    fecha_creacion: datetime = Field(default_factory=ahora_utc)


class ObraSocial(SQLModel, table=True):
    __tablename__ = "obra_social"

    id_obra_social: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    cuit: Optional[str] = Field(default=None, unique=True)
    contacto: Optional[str] = None
    tipo_validacion: str = "manual"
    activo: bool = True


class Caja(SQLModel, table=True):
    __tablename__ = "caja"

    id_caja: Optional[int] = Field(default=None, primary_key=True)
    fecha: date
    empleado_apertura_id: int = Field(foreign_key="empleado.id_empleado")
    hora_apertura: datetime
    monto_apertura: Decimal
    empleado_cierre_id: Optional[int] = Field(default=None, foreign_key="empleado.id_empleado")
    hora_cierre: Optional[datetime] = None
    monto_cierre_declarado: Optional[Decimal] = None
    monto_cierre_sistema: Optional[Decimal] = None
    diferencia: Optional[Decimal] = None
    estado: str = "abierta"


class Venta(SQLModel, table=True):
    __tablename__ = "venta"

    id_venta: Optional[int] = Field(default=None, primary_key=True)
    numero_comprobante: str = Field(unique=True)
    clave_operacion: Optional[str] = Field(default=None, unique=True)
    fecha: datetime = Field(default_factory=ahora_utc)
    empleado_id: int = Field(foreign_key="empleado.id_empleado")
    cliente_id: Optional[int] = Field(default=None, foreign_key="cliente.id_cliente")
    obra_social_id: Optional[int] = Field(default=None, foreign_key="obra_social.id_obra_social")
    caja_id: int = Field(foreign_key="caja.id_caja")
    medio_pago: str
    subtotal: Decimal
    monto_cobertura: Decimal = Decimal("0")
    monto_gravado: Decimal = Decimal("0")
    monto_exento: Decimal = Decimal("0")
    total_a_pagar: Decimal
    receta_verificada: bool = False
    estado: str = "confirmada"
    empleado_anulacion_id: Optional[int] = Field(default=None, foreign_key="empleado.id_empleado")
    fecha_anulacion: Optional[datetime] = None


class DetalleVenta(SQLModel, table=True):
    __tablename__ = "detalle_venta"

    id_detalle_venta: Optional[int] = Field(default=None, primary_key=True)
    venta_id: int = Field(foreign_key="venta.id_venta")
    producto_id: int = Field(foreign_key="producto.id_producto")
    lote_id: int = Field(foreign_key="lote.id_lote")
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
