# ============================================================
# Hart Console — espacio reproducible (headless, Linux).
#
# Reproduce TODOS los experiments declaradDOS en experiments/configs/ y
# deja datos.csv + summary.md (+ PNGs si matplotlib esta instalado).
#
#   docker build -t hart-console .
#   docker run --rm hart-console                      # reproduce todos
#   docker run --rm hart-console --experiment fear_response
#   docker run --rm hart-console --all --no-plots
#
# (El agente Rust + Java son opcionales; este contenedor servira
#  para validar y compartir la dinamica del orquestador.)
# ============================================================

# Python es el unico requisito real del runner de experiments.
FROM python:3.12-slim

WORKDIR /app

# Dependencias opcionales (matplotlib). El nucleo es stdlib.
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --quiet -r requirements.txt

# Fuentes reales de codigo (no hay binarios ni modelos).
COPY orchestrator ./orchestrator
COPY tools ./tools
COPY experiments ./experiments

# .venv/ .gitignore etc. NO se copian (.dockerignore).

# Comando por defecto: reproducir todos los experiments.
CMD ["python", "tools/run_experiments.py", "--all"]