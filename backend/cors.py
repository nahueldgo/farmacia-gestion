import os

# Orígenes de la aplicación de escritorio: el servidor de Vite en desarrollo y, ya instalada,
# un archivo local, cuyo origen el navegador informa como "null".
ORIGENES_POR_DEFECTO = "http://localhost:5173,null"


def origenes_permitidos() -> list[str]:
    texto = os.getenv("ORIGENES_PERMITIDOS") or ORIGENES_POR_DEFECTO
    return [origen.strip() for origen in texto.split(",") if origen.strip()]
