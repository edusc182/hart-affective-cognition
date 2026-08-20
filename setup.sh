#!/usr/bin/env bash
# ============================================================
# setup.sh — prepara Hart Console en Linux/macOS.
#
#   Uso:  ./setup.sh            (o   bash setup.sh)
#
#   1) Compila el agente Java (java_body) — necesario para correr el cuerpo.
#   2) Crea un entorno Python (.venv/) + dependencias opcionales.
#
#   (puntagente Rust:  cd hart_agent && cargo run --release  — opcional)
# ============================================================
set -e
cd "$(dirname "$0")"

say() { printf "\n=== %s ===\n" "$1"; }

# --- 1) Java (cuerpo) ---
say "1/2 - Compuesto agente Java (java_body)"
if command -v javac >/dev/null 2>&1; then
  mkdir -p java_body/classes
  javac -cp "lib/gson-2.13.1.jar" -d java_body/classes java_body/*.java
  echo "ok: java_body/ compilado (clases en java_body/classes/)."
else
  echo "!  No se encontro javac; sal . (instala JDK 8+, o docker para el runner)."
fi

# --- 2) Python + venv ---
say "2/2 — Python (.venv + deps opcionales)"
if command -v python3 >/dev/null 2>&1; then
  [ -d .venv ] || python3 -m venv .venv
  .venv/bin/pip install --quiet -r requirements.txt
  echo "ok: .venv/ listo. Ejecuta el orquestador con:  .venv/bin/python orchestrator/orchestrator.py"
else
  echo "!  No hay python3; salta (runner de experiments requiere Python)."
fi

echo
echo "Listo. Consulta README.md para ejecutar con Java/Python o con Docker."