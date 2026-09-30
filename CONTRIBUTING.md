# Contribuir

¡Gracias por querer ayudarnos! Esto es lo que debes saber.

## Cómo probar antes de cambiar algo

1. **Tests unitarios/regresion** (no necesitan Java ni Rust):

   ```sh
   python -m pip install -r requirements-dev.txt
   python -m pytest tests/unit -q
   ```

   La suite fija la **trayectoria** de los 4 experimentos (regresión) y comprueba los
   **invariantes** del orquestador real y el **contrato del protocolo** (Fase 3c).
2. **Experimenta**: `python3 tools/run_experiments.py --all --no-plots` es la vía más rápida
   de verificar que la dinámica afectiva sigue siendo estable (vale sin Rust/Java).
3. **Compila Java** (convención única: las clases van a `java_body/classes/`):
   - Linux/macOS: `javac -cp "lib/gson-2.13.1.jar" -d java_body/classes java_body/*.java`
   - Windows: `javac -cp "lib\gson-2.13.1.jar" -d java_body\classes java_body\*.java`

   **Nunca** compiles "in place" (sin `-d`): genera `.class` junto a las fuentes y duplica
   la convención (es exactamente lo que `INIT_LIFE.bat` ya no hace).
4. **(Opcional) Rust**: `cd hart_agent && cargo check` (los modelos GGUF NUNCA se suben).
5. **Integracion real Java <-> Python** (Fase 3c): requiere JDK + clases compiladas + **display**.

   ```sh
   python -m pytest tests/integration -q      # display ausente -> skip explicito
   python tools/run_integration.py --cycles 6 # evidencia en experiments/results/integration/
   ```

   Java se trata como **proceso externo** (no se importa ni se simula). Criterios:
   display -> RUN, sin display -> SKIP, Java/TCP/telemetria mal -> **FAIL**.
   La parada del proceso esta verificada: no deja JVM, ventana ni puerto huerfano.

La CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) ejecuta esto mismo en cada
push/PR: experimentos reproducibles, `pytest tests/unit`, integracion bajo `xvfb-run`, `javac`
y `cargo check`, **sin descargar ningún GGUF**.

## Reglas de oro

- **El valor es la arquitectura y la reproducibilidad.** No añadas "magia": cualquier
  dinámica nueva debe poder medirse con un experimento nuevo en `experiments/configs/`.
- **No reescribas la lógica interna** desde un runner: `tools/run_experiments.py` IMPORTA
  el orquestador real; no lo re-importa con heurísticas paralelas.
- **Telemetría opt-in**: si expones un campo diagnóstico (p.ej. `saturationFactor` en
  Java), hazlo opcional y documentalo (Java: `-DHART_TELEMETRY=true`).

## Convenciones

- Mensajes de commit en **inglés**, imperativo y conciso (`feat:`, `fix:`, `docs:`, `test:`).
- Los binarios (`*.class`, `.jar`, `target/`, `.venv/`, GGUF) van en `.gitignore` / Docker.
  `lib/gson-2.13.1.jar` es la **única** excepción versionada (necesaria para compilar Java).
- `requirements.txt` refleja solo deps opcionales — el núcleo es stdlib. Las de desarrollo
  (pytest) viven en `requirements-dev.txt`.
- Compilación Java con **una sola convención**: `-d java_body/classes`. `INIT_LIFE.bat`,
  `setup.sh` y la CI ya la usan; no dejes `.class` junto a las fuentes.
- La documentación de estado (p. ej. `docs/phase3_design.md`) debe reflejar lo que **realmente
  está implementado y verificado**; si algo no se ha ejecutado, se marca como no verificado.

## Problemas / ideas

Usa las *Issues* de GitHub. Etiquetas sugeridas: `experiment`, `telemetry`, `docs`,
`bug`, `orchestrator`, `rust agent`. No subas modelos GGUF al repo (varios GB).