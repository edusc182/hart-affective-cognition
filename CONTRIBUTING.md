# Contribuir

¡Gracias por querer ayudarnos! Esto es lo que debes saber.

## Cómo probar antes de cambiar algo

1. **Experimenta**: `python3 tools/run_experiments.py --all` es la vía más rápida
   de verificar que la dinámica afectiva sigue siendo estable (vale Cero sin Rust/Java).
2. **Compila Java**: `javac -cp "lib/gson-2.13.1.jar" -d java_body/classes java_body/*.java`.
3. **(Opcional) Set de Rust**: `cd hart_agent && cargo build` (los modelos GGUF NUNCA se suben).

## Reglas de oro

- **El valor es la arquitectura y la reproducibilidad.** No añadas "magia": cualquier
  dinámica nueva debe poder medirse con un experimento nuevo en `experiments/configs/`.
- **No reescribas la lógica interna** desde un runner: `tools/run_experiments.py` IMPORTA
  el orquestador real; no lo re-importa con heurísticas paralelas.
- **Telemetría opt-in**: si expones un campo diagnóstico (p.ej. `saturationFactor` en
  Java), hazlo opcional y documentalo (Java: `-DHART_TELEMETRY=true`).

## Convenciones

- Mensajes de commit en **inglés**, imperativo y conciso (`feat:`, `fix:`, `docs:`, `test:`).
- Los binarios (`*.class`, `.jar`, `target/`, `.venv/`, GGUF 大) van en `.gitignore` / Docker.
- `REQUIREMENTS.txt` refleja solo deps opcionales — el núcleo es stdlib.

## Problemas / ideas

Usa las *Issues* de GitHub. Etiquetas sugeridas: `experiment`, `telemetry`, `docs`,
`bug`, `orchestrator`, `ruster agent`. No subas modelos GGUF al repo (varios GB).