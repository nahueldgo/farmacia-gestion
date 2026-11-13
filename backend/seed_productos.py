from datetime import timedelta
from decimal import Decimal
from typing import Optional

from sqlmodel import Session, select

from db import engine
from fechas import hoy
from models import (
    CategoriaCoberturaObraSocial,
    ClaseTerapeutica,
    CondicionIva,
    FormaFarmaceutica,
    Laboratorio,
    Lote,
    Medicamento,
    MedicamentoClaseTerapeutica,
    ObraSocial,
    PrincipioActivo,
    Producto,
    ReglaCobertura,
)

# Datos de demostración para desarrollo y para probar el sistema con productos y obras sociales cargados.
# No forma parte del arranque de producción: se ejecuta a mano, una sola vez, y solo para una demostración. No crea
# usuarios ni contraseñas. Las obras sociales tienen nombres inventados que evocan entidades reales; los
# medicamentos usan nombre genérico y presentaciones habituales (muchas tomadas de vademécums publicados por la Cámara de
# Farmacias de la Provincia de Córdoba); los laboratorios y los precios de los medicamentos son aproximados, y los
# precios de perfumería y cuidado personal son de farmacias online argentinas. Cubre las 7 categorías de cobertura, las 18
# clases terapéuticas y los tipos de producto. Algunos medicamentos quedan sin clase a propósito: el catálogo de clases se
# simplificó y no tiene la que les corresponde (ver docs/03). Se puede ejecutar varias veces: no duplica.

EXENTO = "exento"
GRAVADO_21 = "gravado_21"
STOCK_MINIMO = 10

# nombre, principio activo, concentración, forma farmacéutica, categoría de cobertura, laboratorio, precio, requiere
# receta, clases terapéuticas, lotes (número, días hasta el vencimiento, cantidad); con días negativos el lote ya está
# vencido y con cantidad 0 está agotado.
MEDICAMENTOS = [
    ("Ibuprofeno 400 mg x 20 comprimidos", "Ibuprofeno", "400 mg", "Comprimido", "ambulatorio", "Roemmers", "6500.00", True,
     ["Antiinflamatorio", "Analgésico"], [("IB-2605", 25, 15), ("IB-2701", 400, 80)]),
    ("Paracetamol 500 mg x 16 comprimidos", "Paracetamol", "500 mg", "Comprimido", "ambulatorio", "Bagó", "4200.00", False,
     ["Analgésico"], [("PA-2509", -12, 10), ("PA-2703", 500, 120)]),
    ("Amoxicilina 500 mg x 16 comprimidos", "Amoxicilina", "500 mg", "Comprimido", "ambulatorio", "Siegfried", "11500.00", True,
     ["Antibiótico"], [("AM-2702", 300, 60)]),
    ("Loratadina 10 mg x 10 comprimidos", "Loratadina", "10 mg", "Comprimido", "ambulatorio", "Roemmers", "3800.00", False,
     ["Antihistamínico"], [("LO-2717", 450, 70)]),
    ("Omeprazol 20 mg x 28 cápsulas", "Omeprazol", "20 mg", "Cápsula", "ambulatorio", "Gador", "7900.00", True,
     ["Antiácido y protector gástrico"], [("OM-2718", 420, 65)]),
    ("Alprazolam 0,5 mg x 30 comprimidos", "Alprazolam", "0,5 mg", "Comprimido", "ambulatorio", "Roemmers", "6400.00", True,
     ["Ansiolítico"], [("AL-2719", 380, 40)]),
    ("Fluconazol 150 mg x 1 cápsula", "Fluconazol", "150 mg", "Cápsula", "ambulatorio", "Bagó", "5200.00", True,
     ["Antifúngico"], [("FL-2720", 410, 55)]),
    ("Salbutamol 100 mcg aerosol x 200 dosis", "Salbutamol", "100 mcg", "Aerosol", "ambulatorio", "Raffo", "7100.00", True,
     ["Broncodilatador"], [("SA-2721", 390, 45)]),
    ("Prednisona 20 mg x 30 comprimidos", "Prednisona", "20 mg", "Comprimido", "ambulatorio", "Elea", "6300.00", True,
     ["Corticoide"], [("PR-2722", 430, 50)]),
    ("Hioscina 10 mg x 20 comprimidos", "Hioscina", "10 mg", "Comprimido", "ambulatorio", "Raffo", "5500.00", False,
     ["Antiespasmódico"], [("HI-2723", 440, 60)]),
    ("Enalapril 10 mg x 30 comprimidos", "Enalapril", "10 mg", "Comprimido", "cronico", "Bagó", "7800.00", True,
     ["Antihipertensivo"], [("EN-2703", 380, 90)]),
    ("Atorvastatina 20 mg x 30 comprimidos", "Atorvastatina", "20 mg", "Comprimido", "cronico", "Gador", "14500.00", True,
     ["Hipolipemiante"], [("AT-2704", 420, 70)]),
    ("Levotiroxina 100 mcg x 50 comprimidos", "Levotiroxina", "100 mcg", "Comprimido", "cronico", "Elea", "9800.00", True,
     [], [("LE-2702", 350, 50)]),
    ("Sertralina 50 mg x 30 comprimidos", "Sertralina", "50 mg", "Comprimido", "cronico", "Gador", "12800.00", True,
     ["Antidepresivo"], [("SE-2724", 370, 40)]),
    ("Acenocumarol 4 mg x 20 comprimidos", "Acenocumarol", "4 mg", "Comprimido", "cronico", "Siegfried", "9600.00", True,
     ["Anticoagulante"], [("AC-2725", 360, 35)]),
    ("Furosemida 40 mg x 20 comprimidos", "Furosemida", "40 mg", "Comprimido", "cronico", "Bagó", "3900.00", True,
     ["Diurético"], [("FU-2726", 400, 55)]),
    ("Metformina 850 mg x 30 comprimidos", "Metformina", "850 mg", "Comprimido", "diabetes_insulina", "Raffo", "6900.00", True,
     ["Antidiabético"], [("ME-2705", 450, 100)]),
    ("Glibenclamida 5 mg x 30 comprimidos", "Glibenclamida", "5 mg", "Comprimido", "diabetes_insulina", "Siegfried", "5600.00", True,
     ["Antidiabético"], [("GL-2704", 400, 60)]),
    ("Insulina NPH 100 UI/ml x 10 ml", "Insulina NPH", "100 UI/ml", "Solución inyectable", "diabetes_insulina", "Elea", "25000.00", True,
     ["Antidiabético"], [("IN-2606", 200, 3)]),
    ("Tamoxifeno 20 mg x 30 comprimidos", "Tamoxifeno", "20 mg", "Comprimido", "oncologico", "Bagó", "18500.00", True,
     [], [("TA-2706", 360, 30)]),
    ("Anastrozol 1 mg x 28 comprimidos", "Anastrozol", "1 mg", "Comprimido", "oncologico", "Teva Argentina", "26000.00", True,
     [], [("AN-2707", 390, 24)]),
    ("Letrozol 2,5 mg x 28 comprimidos", "Letrozol", "2,5 mg", "Comprimido", "oncologico", "Teva Argentina", "27500.00", True,
     [], [("LT-2608", 330, 0)]),
    ("Levonorgestrel + Etinilestradiol x 21 comprimidos", "Levonorgestrel + Etinilestradiol", "0,15 mg + 0,03 mg", "Comprimido",
     "anticonceptivos", "Gador", "8900.00", True, ["Anticonceptivo"], [("LV-2709", 480, 60)]),
    ("Drospirenona + Etinilestradiol x 28 comprimidos", "Drospirenona + Etinilestradiol", "3 mg + 0,03 mg", "Comprimido",
     "anticonceptivos", "Bayer", "19500.00", True, ["Anticonceptivo"], [("DR-2710", 500, 45)]),
    ("Levonorgestrel 1,5 mg x 1 comprimido", "Levonorgestrel", "1,5 mg", "Comprimido", "anticonceptivos", "Elea", "9800.00", False,
     ["Anticonceptivo"], [("LN-2711", 520, 40)]),
    ("Lamivudina 150 mg x 60 comprimidos", "Lamivudina", "150 mg", "Comprimido", "hiv", "Gador", "25000.00", True,
     ["Antiviral"], [("LA-2712", 300, 40)]),
    ("Efavirenz 600 mg x 30 comprimidos", "Efavirenz", "600 mg", "Comprimido", "hiv", "Roemmers", "28000.00", True,
     ["Antiviral"], [("EF-2713", 310, 35)]),
    ("Baclofeno 10 mg x 60 comprimidos", "Baclofeno", "10 mg", "Comprimido", "discapacidad", "Ariston", "12500.00", True,
     [], [("BA-2714", 360, 50)]),
    ("Carbamazepina 200 mg x 60 comprimidos", "Carbamazepina", "200 mg", "Comprimido", "discapacidad", "Novartis", "11800.00", True,
     [], [("CA-2715", 380, 45)]),
    ("Valproato de magnesio 200 mg x 60 comprimidos", "Valproato de magnesio", "200 mg", "Comprimido", "discapacidad",
     "Teva Argentina", "15800.00", True, [], [("VA-2716", 340, 40)]),
]

# nombre, tipo de producto, precio, lotes (número, días hasta el vencimiento, cantidad); sin cobertura y con IVA al 21 %.
OTROS_PRODUCTOS = [
    ("Shampoo hidratación 400 ml", "perfumeria", "7793.50", [("SH-2801", 700, 60)]),
    ("Crema hidratante corporal 200 ml", "perfumeria", "9500.00", [("CR-2802", 650, 45)]),
    ("Protector solar FPS 50 x 50 ml", "perfumeria", "29755.00", [("PS-2803", 600, 30)]),
    ("Jabón de tocador 90 g", "perfumeria", "2373.87", [("JA-2804", 900, 150)]),
    ("Cepillo dental suave", "cuidado_personal", "2999.50", [("CE-2805", 1500, 80)]),
    ("Repelente de insectos en aerosol 140 ml", "cuidado_personal", "3821.13", [("RE-2806", 800, 50)]),
    ("Termómetro digital", "otro", "8900.00", [("TE-2807", 1800, 25)]),
]

# Porcentaje de cobertura por categoría, en este orden. None: la obra social no tiene regla para esa categoría.
CATEGORIAS = ["ambulatorio", "cronico", "diabetes_insulina", "oncologico", "anticonceptivos", "hiv", "discapacidad"]
OBRAS_SOCIALES = {
    "PreMedix": [50, 80, 100, 100, 100, 100, 100],
    "Hominia": [60, 85, 100, 100, None, 100, 100],
    "DoctoNet": [40, 70, None, None, None, None, None],
    "Amfra Salud": [40, 70, 100, 100, 100, 100, 100],
    "OSSACRO": [50, 80, 100, 100, 100, None, None],
    "Jerarca Salud": [70, 90, 100, 100, 100, 100, 100],
}


def obtener_o_crear(session: Session, modelo, **datos):
    objeto = session.exec(select(modelo).filter_by(**datos)).first()
    if objeto is None:
        objeto = modelo(**datos)
        session.add(objeto)
        session.commit()
        session.refresh(objeto)
    return objeto


def condicion_iva(session: Session, nombre: str) -> CondicionIva:
    return session.exec(select(CondicionIva).where(CondicionIva.nombre == nombre)).one()


def ids_de_categorias(session: Session) -> dict[str, int]:
    return {c.nombre: c.id_categoria_cobertura_obra_social for c in session.exec(select(CategoriaCoberturaObraSocial)).all()}


def producto_por_nombre(session: Session, nombre: str) -> Optional[Producto]:
    return session.exec(select(Producto).where(Producto.nombre == nombre)).first()


def crear_producto(session: Session, lotes: list[tuple[str, int, int]], **datos) -> Producto:
    producto = Producto(stock_minimo=STOCK_MINIMO, **datos)
    session.add(producto)
    session.commit()
    session.refresh(producto)
    for numero, dias, cantidad in lotes:
        session.add(Lote(
            producto_id=producto.id_producto, numero_lote=numero, fecha_vencimiento=hoy() + timedelta(days=dias), cantidad=cantidad
        ))
    session.commit()
    return producto


def vincular_clases(session: Session, id_medicamento: int, clases: list[str]) -> None:
    for nombre in clases:
        clase = session.exec(select(ClaseTerapeutica).where(ClaseTerapeutica.nombre == nombre)).one()
        obtener_o_crear(session, MedicamentoClaseTerapeutica, medicamento_id=id_medicamento, clase_terapeutica_id=clase.id_clase_terapeutica)


def cargar_medicamentos(session: Session) -> int:
    exento = condicion_iva(session, EXENTO)
    categorias = ids_de_categorias(session)
    cargados = 0
    for nombre, droga, concentracion, forma, categoria, laboratorio, precio, receta, clases, lotes in MEDICAMENTOS:
        producto = producto_por_nombre(session, nombre)
        if producto is None:
            producto = crear_producto(
                session, lotes, nombre=nombre, precio=Decimal(precio), condicion_iva_id=exento.id_condicion_iva,
                tipo_producto="medicamento", laboratorio_id=obtener_o_crear(session, Laboratorio, nombre=laboratorio).id_laboratorio,
            )
            session.add(Medicamento(
                producto_id=producto.id_producto,
                principio_activo_id=obtener_o_crear(session, PrincipioActivo, nombre=droga).id_principio_activo,
                concentracion=concentracion,
                forma_farmaceutica_id=obtener_o_crear(session, FormaFarmaceutica, nombre=forma).id_forma_farmaceutica,
                requiere_receta=receta,
                categoria_cobertura_obra_social_id=categorias[categoria],
            ))
            session.commit()
            cargados += 1
        vincular_clases(session, producto.id_producto, clases)
    return cargados


def cargar_otros_productos(session: Session) -> int:
    gravado = condicion_iva(session, GRAVADO_21)
    cargados = 0
    for nombre, tipo, precio, lotes in OTROS_PRODUCTOS:
        if producto_por_nombre(session, nombre) is None:
            crear_producto(session, lotes, nombre=nombre, precio=Decimal(precio), condicion_iva_id=gravado.id_condicion_iva, tipo_producto=tipo)
            cargados += 1
    return cargados


def guardar_regla(session: Session, id_obra_social: int, id_categoria: int, porcentaje: int) -> None:
    regla = session.exec(
        select(ReglaCobertura).where(
            ReglaCobertura.obra_social_id == id_obra_social, ReglaCobertura.categoria_cobertura_obra_social_id == id_categoria
        )
    ).first()
    if regla is None:
        regla = ReglaCobertura(obra_social_id=id_obra_social, categoria_cobertura_obra_social_id=id_categoria, porcentaje_cobertura=0)
    regla.porcentaje_cobertura = Decimal(porcentaje)
    session.add(regla)
    session.commit()


def cargar_obras_sociales(session: Session) -> int:
    categorias = ids_de_categorias(session)
    nuevas = 0
    for nombre, porcentajes in OBRAS_SOCIALES.items():
        existente = session.exec(select(ObraSocial).where(ObraSocial.nombre == nombre)).first()
        nuevas += existente is None
        obra_social = existente or obtener_o_crear(session, ObraSocial, nombre=nombre)
        for categoria, porcentaje in zip(CATEGORIAS, porcentajes):
            if porcentaje is not None:
                guardar_regla(session, obra_social.id_obra_social, categorias[categoria], porcentaje)
    return nuevas


def cargar_datos_de_demostracion():
    with Session(engine) as session:
        print("Medicamentos nuevos:", cargar_medicamentos(session))
        print("Otros productos nuevos:", cargar_otros_productos(session))
        print("Obras sociales nuevas:", cargar_obras_sociales(session))


if __name__ == "__main__":
    cargar_datos_de_demostracion()
