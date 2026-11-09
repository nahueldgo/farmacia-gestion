from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from servicios.base_ventas import a_centavos

CERO = Decimal("0")
CIEN = Decimal("100")


# Lo que el motor recibe de cada producto: cuánto cuesta la línea y a qué categoría de cobertura pertenece.
@dataclass(frozen=True)
class LineaACubrir:
    importe: Decimal
    categoria_id: Optional[int] = None  # None: el producto no tiene categoría y se paga completo


@dataclass(frozen=True)
class LineaCubierta:
    importe: Decimal
    porcentaje: Decimal
    cobertura: Decimal  # lo que paga la obra social
    copago: Decimal  # lo que paga el cliente


@dataclass(frozen=True)
class ResultadoCopago:
    lineas: list[LineaCubierta]
    cobertura: Decimal
    copago: Decimal  # el total a cobrar al cliente


# Patrón Strategy: cada estrategia responde un solo dato, qué porcentaje cubre la obra social de una línea.
# El cálculo de los montos es el mismo para todas y está en calcular_copago.
class EstrategiaCobertura(ABC):
    @abstractmethod
    def porcentaje(self, linea: LineaACubrir) -> Decimal: ...


# Por defecto: el porcentaje sale de las reglas que el farmacéutico cargó a mano para la obra social.
# Sin categoría o sin regla para la categoría, no cubre nada.
class EstrategiaManual(EstrategiaCobertura):
    def __init__(self, reglas: dict[int, Decimal]):
        self._reglas = reglas

    def porcentaje(self, linea: LineaACubrir) -> Decimal:
        if linea.categoria_id is None:
            return CERO
        return self._reglas.get(linea.categoria_id, CERO)


# Una estrategia nueva (por ejemplo, la que consulte a un validador externo) se agrega acá con el
# valor de tipo_validacion que le corresponda.
ESTRATEGIAS: dict[str, type[EstrategiaCobertura]] = {"manual": EstrategiaManual}


# Elige la estrategia según el tipo_validacion de la obra social; si no hay una para ese tipo, usa la manual.
def elegir_estrategia(tipo_validacion: str, reglas: dict[int, Decimal]) -> EstrategiaCobertura:
    return ESTRATEGIAS.get(tipo_validacion, EstrategiaManual)(reglas)


def calcular_copago(lineas: list[LineaACubrir], estrategia: EstrategiaCobertura) -> ResultadoCopago:
    cubiertas = []
    for linea in lineas:
        porcentaje = estrategia.porcentaje(linea)
        if not CERO <= porcentaje <= CIEN:
            raise ValueError(f"El porcentaje de cobertura debe estar entre 0 y 100, y la estrategia dio {porcentaje}")
        # Se redondea cada línea, así la suma de las líneas es siempre igual al total.
        cobertura = a_centavos(linea.importe * porcentaje / CIEN)
        cubiertas.append(LineaCubierta(linea.importe, porcentaje, cobertura, linea.importe - cobertura))
    return ResultadoCopago(
        lineas=cubiertas,
        cobertura=sum((c.cobertura for c in cubiertas), CERO),
        copago=sum((c.copago for c in cubiertas), CERO),
    )
