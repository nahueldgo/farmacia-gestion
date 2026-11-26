#!/usr/bin/env bash
# Crea la base completa de una sola vez, sobre una base vacía (por ejemplo, la de la nube).
# Ejecuta todos los archivos de database/ en orden de nombre, igual que Docker.
# Si algo falla, se corta y no queda nada creado.
#
# Uso: bash scripts/crear_base.sh "URL_DE_LA_BASE"

set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo 'Uso: bash scripts/crear_base.sh "URL_DE_LA_BASE"' >&2
    exit 1
fi

carpeta="$(dirname "$0")/../database"

archivos=()
for archivo in "$carpeta"/*.sql; do
    archivos+=(-f "$archivo")
done

export PGCLIENTENCODING=UTF8

psql "$1" --quiet --set=ON_ERROR_STOP=1 --single-transaction "${archivos[@]}"

echo "Base creada."
