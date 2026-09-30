# Fase 3 — Estado de implementación (especificación viva)

> Este documento describe **lo que está realmente implementado y verificado**, no lo que se
> pretende hacer. Última verificación: **2026-09-30**, commit `b7026f4`, Python 3.14.6,
> matplotlib 3.10.9, JDK 21.0.6.
>
> 🛑 **Regla de oro (sin cambios):** la Fase 3 **mide el sistema existente; no lo modifica ni
> lo reimplementa.** Toda instrumentación añadida es **opt-in y desactivable**
> (`-DHART_TELEMETRY=true`) y no altera ninguna dinámica.

## 1. Estado por sub-fase

| Sub-fase | Alcance | Estado |
|----------|---------|--------|
| **3a** | Runner + CSV (orquestador real *in-process*, LLM desactivado) | ✅ **Implementada y ejecutada** |
| **3b** | Gráficas PNG + `summary.md` por experimento | ✅ **Implementada y ejecutada** |
| **3c** | Integración TCP real (Java ↔ Python) como **validación automatizada** | ❌ **Único hueco funcional de la fase** |
| **3d** | Telemetría de saturación (`saturationFactor`, `repeatCount`, `switchRate`) | ✅ **Implementada (opt-in)** |

### 1.1 Precisión sobre 3c

El **protocolo** Java↔Python está **definido y alineado campo a campo** en ambos lados
(verificado por `tests/test_protocol_contract.py`), y el flujo real existe: los dos procesos
se hablan por TCP/JSON cuando se lanzan con `INIT_LIFE.bat`.

Lo que **no existe** es una prueba automatizada que demuestre el comportamiento del protocolo
en ejecución real y capture su salida:

- **protocolo diseñado y mutuamente consistente** … sí
- **integración ejecutada y verificada por un test** … **no**

La trayectoria experimental validada hoy es **in-process** (el runner importa el orquestador).
Ese es el límite actual de la evidencia, y es exactamente lo que cierra la Fase 3c.

## 2. Objetivo

Producir **evidencia reproducible** de que las dinámicas ya programadas (valencia, momentum,
habituación, motor, sensibilidad) generan comportamientos **medibles y distintos** según el
estado interno — sin volver a escribirlas.

## 3. Principio de ejecución (verificado en el código)

- `tools/run_experiments.py` **importa y reutiliza el `CognitiveOrchestrator` real**
  (`from orchestrator.orchestrator import CognitiveOrchestrator`) en proceso. No reescribe
  fórmulas: llama a sus métodos públicos (`perceive_and_update`, `generate_internal_monologue`,
  `apply_feedback`, `compute_motor_output`, `compute_sensor_sensitivity`,
  `compute_agent_state`, `apply_boredom_drive`).
- El LLM se **desactiva por defecto** (`model_path=None` → `heuristic_response`): así se prueba
  la **dinámica programada**, no la del modelo.
- Cada experimento es un **script de estímulo determinista** (luz / distancia / delta afectivo
  por ciclo) → resultados **reproducibles** (`seed` fijo).
- La reproducibilidad está **fijada por tests**
  (`tests/test_orchestrator_invariants.py::test_trajectory_is_deterministic`).

## 4. Mapa de métricas → fuente real (con estado por columna)

| Columna del CSV | Fuente real | Estado |
|-----------------|-------------|--------|
| `cycle` | contador interno del runner | ✅ |
| `timestamp` | runner (segundos desde el inicio del run) | ✅ |
| `sequence` | `payload.sequence` / memoria del orquestador | ✅ |
| `light_level` | `state["light_level"]` | ✅ |
| `distance` | `state["proximity_to_object_meters"]` | ✅ |
| `current_action` | acción devuelta por el orquestador | ✅ |
| `affective_valence` | `state["affective_valence"]` (clampeada a ±1) | ✅ |
| `affective_momentum` | `historical_inertia` | ✅ |
| `motor_output` | `compute_motor_output()` (0.3–1.5) | ✅ |
| `sensor_sensitivity` | `compute_sensor_sensitivity()` (0.5–1.8) | ✅ |
| `agent_state` | `compute_agent_state()` | ✅ |
| `direct_affective_change` | `direct_delta` del feedback | ✅ |
| `effective_affective_change` | `effective_delta` (mezcla con inercia) | ✅ |
| `historical_inertia` | `compute_historical_inertia()` | ✅ |
| `repeat_count` | observación del runner sobre la secuencia de acciones | ✅ |
| `switch_rate` | observación del runner sobre la secuencia de acciones | ✅ |
| `saturation_factor` | `FeedbackMessage.saturationFactor` (**solo Java**) | ⚠️ **vacía** *in-process* → cierra en **3c** |
| `thought` | `generate_internal_monologue()` (heurística sin LLM) | ✅ |
| `rationale` | `feedback_payload["rationale"]` | ✅ |

## 5. Runner — CLI real

```sh
python tools/run_experiments.py --experiment fear_response   # un experimento
python tools/run_experiments.py --all                        # los 4 experimentos
python tools/run_experiments.py --all --no-plots              # solo CSV + summary
```

Argumentos implementados: `--experiment <name>`, `--all`, `--no-plots` (los dos primeros son
mutuamente excluyentes y obligatorios entre sí). **No existe `--gui`**: aparecía en la versión
anterior de este documento y se elimina de la especificación (las gráficas se guardan como PNG,
no se abren ventanas).

## 6. Esquema de configuración (real)

Un archivo por experimento en `experiments/configs/<name>.json`:

```jsonc
{
  "name": "fear_response",
  "description": "Low light + distant object with sustained negative affective pressure...",
  "category": "affective_dynamics",
  "llm": "disabled",              // se prueba la dinámica programada, no el modelo
  "seed": 42,                     // reproducibilidad
  "initial_state": { "affective_valence": -0.20, "affective_momentum": 0.0 },
  "stimulus": {
    "light_level": ["Bajo", "Bajo", "Bajo", "Bajo", "Bajo", "Bajo"],
    "distance": [3.2, 3.0, 3.5, 3.8, 3.1, 3.9],
    "affective_change": [-0.12, -0.20, -0.25, -0.30, -0.22, -0.28]
  },
  "cycles": 6
}
```

> `affective_change` **no** reimplementa el modelo afectivo: es el estímulo de entrada que
> `CharacterBody.evaluateAffectiveFeedback` habría producido en esa situación.

## 7. Layout de salida (real)

```text
experiments/
├── configs/<name>.json                 # estímulo reproducible (versionado)
├── docs/<name>.md                      # informe humano del experimento (versionado)
└── results/<name>/                     # generado; ignorado por git
    ├── config.json                     # copia de la config usada
    ├── data.csv                        # 19 columnas por ciclo
    ├── summary.md                      # resumen + cómo reproducir
    └── plots/valence.png               # solo con matplotlib y sin --no-plots
        plots/behavior.png
```

## 8. Resultados medidos (evidencia)

Comando: `python tools/run_experiments.py --all --no-plots` (verificado el 2026-09-30).

| Experimento | Ciclos | valencia final | momentum | motor | sensibilidad | estado |
|-------------|--------|----------------|----------|-------|--------------|--------|
| `affective_momentum` | 6 | +0.0604 | −0.0524 | 0.9085 | 1.0000 | `neutral` |
| `exploration_response` | 4 | +0.6436 | +0.1352 | 1.1226 | 0.8000 | `exploratory` |
| `fear_response` | 6 | **−1.0000** | −0.2234 | **0.5732** | **1.8000** | `panic_avoidance` |
| `habituation` | 8 | +0.3107 | +0.0490 | 1.0029 | 1.0000 | `curious` |

`fear_response` reproduce la "paradoja realista": la valencia cae hasta el clamp inferior, el
**motor se frena** (0.8214 → 0.5732) y la **sensibilidad sube** (1.0 → 1.8). `habituation` fuerza
la acción `"Explorar el entorno buscando nuevos estimulos"` en el ciclo 6 (sexto ciclo cómodo),
con `repeat_count` reiniciado a 1. Estos valores están **fijados como regression tests** en
`tests/test_regression_experiments.py`.

## 9. Fase 3c — especificación pendiente (único hueco funcional)

Objetivo: cerrar la Fase 3 con **una prueba automatizada de la integración real**, no con más
instrumentación.

```text
Python experiment/test
       │  TCP/JSON
       ▼
CognitiveSocketBridge (Java)
       │
       ▼
CharacterBody (Java)
       │  FeedbackMessage
       ▼
orquestador Python
       │
       ▼
experiments/results/<name>/data.csv  ← saturation_factor / repeat_count / switch_rate
```

Entregables:

1. Un runner de integración (p. ej. `tools/run_integration.py`) que lance Java y Python como
   procesos reales, espere la convergencia y **cierre todo de forma fiable** (sin ventanas
   colgadas ni procesos huérfanos).
2. Un test que **sustituya** a
   `tests/test_protocol_contract.py::test_saturation_column_is_still_empty_in_the_in_process_trajectory`
   (ese test existe precisamente para fallar cuando 3c aterrice) y compruebe que los valores de
   `saturationFactor`, `repeatCount` y `switchRate` emitidos por Java aparecen en el CSV de
   Python, coherentes con `repeat_count` / `switch_rate` observados por el runner.

Criterios de aceptación:

- El test es determinista y **no requiere GPU ni GGUF**.
- Si Java no puede arrancar en el entorno (p. ej. CI sin display), el test se marca como *skip*
  explícito, nunca como *pass* silencioso.
- La dinámica del orquestador **no cambia**: 3c solo observa (los regression tests del §8 deben
  seguir pasando sin tocar sus valores esperados).

Restricciones: no se reescribe la lógica afectiva; la telemetría sigue siendo opt-in.

## 10. Evidencia de validez (regla de oro)

- El runner **nunca** calcula `motor` / `sensitivity` / `valence` con fórmulas propias.
- Si `orchestrator.py` cambia su lógica, los resultados cambian automáticamente → la evidencia
  sigue siendo fiel (y los regression tests fallan a propósito para forzar la revisión).
- `tests/test_protocol_contract.py` fija el contrato del protocolo en **ambos** lados (fuentes
  Java + consumidor Python): un cambio de nombre de campo rompe el test.
- Los invariantes (`valence ∈ [-1, 1]`, `motor ∈ [0.3, 1.5]`, `sensor ∈ [0.5, 1.8]`, estados
  válidos, `switch_rate ∈ [0, 1]`) se comprueban en **cada ciclo** de **cada** experimento.

## 11. Decisiones ya aplicadas (histórico de §10 de la versión anterior)

| Decisión pendiente (versión antigua de este doc) | Estado |
|--------------------------------------------------|--------|
| ¿Runner con el orquestador real *in-process* y TCP solo como validación? | ✅ **Aplicada**: es lo que hace `run_experiments.py` |
| ¿Incluir `saturation_factor` (pequeña instrumentación en Java)? | ✅ **Aplicada (3d)**: viaja en `FeedbackMessage`, opt-in |
| ¿Gráficas con matplotlib o solo CSV + tabla ASCII? | ✅ **Aplicada**: matplotlib **opcional**; CSV y `summary.md` siempre |
| Flag `--gui` en la vía de ejecución | ❌ **Descartada**: nunca se implementó; no forma parte de la CLI real |

## 12. Cómo verificar este documento

```sh
python -m pytest tests -q                                  # 94 tests (93 pasan, 1 skip)
python tools/run_experiments.py --all --no-plots           # 4 CSV + summaries
javac -cp "lib/gson-2.13.1.jar" -d java_body/classes java_body/*.java
cd hart_agent && cargo check                               # agente cognitivo (sin GGUF)
```

La CI ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)) ejecuta estos cuatro pasos en
cada push/PR, **sin descargar ningún modelo GGUF**.

