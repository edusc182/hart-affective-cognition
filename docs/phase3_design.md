# Fase 3 — Diseño (en revisión; sin implementar todavía)

> 🛑 Regla de oro: **Fase 3 mide el sistema existente; no lo modifica ni lo reimplementa.**
> La lógica cognitiva/afectiva sigue siendo idéntica. Cualquier cambio propuesto aquí es
> *instrumentación opcional y desactivable* (no altera dinámicas) y debe revisarse antes de aplicarse.

## 1. Objetivo

Producir **evidencia reproducible** de que las dinámicas ya programadas
(valencia, momentum, habituación, motor, sensibilidad) generan comportamientos
**medibles y distintos** según el estado interno — sin volver a escribirlas.

## 2. Principio de ejecución

- `run_experiments.py` **importa y reutiliza el `CognitiveOrchestrator` real**
  (`orchestrator/orchestrator.py`) en proceso. No reescribe fórmulas: llama a sus
  métodos públicos (`perceive_and_update`, `apply_feedback`, `compute_motor_output`,
  `compute_sensor_sensitivity`, `compute_agent_state`, `apply_boredom_drive`).
- El LLM se **desactiva por defecto** (`model_path=None` → `heuristic_response`),
  así se prueba la **dinámica programada**, no la del modelo.
- Cada experimento es un **script de estímulo determinista** (luz/distancia/delta afectivo
  por ciclo) → resultados **reproducibles** (seed).
- Opcionalmente, una **pasarela de integración** lanza los procesos reales Java+Python por
  TCP y parsea `stdout`; usada solo para validar extremo-a-extremo.

## 3. Mapa de métricas (columna) → fuente real

| Métrica | Fuente / origen |
|---------|-----------------|
| `cycle` | contador interno del runner |
| `timestamp` | runner (epoch) |
| `sequence` | `payload.sequence` (orquestador recuerda el último) |
| `light_level` | `state["light_level"]` |
| `distance` | `state["proximity_to_object_meters"]` |
| `action` / `current_action` | `state["current_action"]` / `actionTaken` del feedback |
| `affective_valence` | `state["affective_valencia"]` |
| `affective_momentum` | `historical_inertia` |
| `motor_output` | `compute_motor_output()` |
| `sensor_sensitivity` | `compute_sensor_sensitivity()` |
| `agent_state` | `compute_agent_state()` |
| `direct_affective_change` | `direct_delta` del feedback |
| `effective_affective_change` | `effective_delta` |
| `saturation_factor` | ⚠️ **Solo Java** (`computeSaturationFactor`). No expuesto a Python aún. |
| `thought` | stdout `Monólogo Interno` (cuando LLM activo) |
| `rationale` | `feedback_payload["rationale"]` |

### Nota sobre `saturation_factor`
No está disponible en la ruta Python. Para incluirlo sin tocar lógica, se propondría
(únicamente) **emitir un campo `saturationFactor` en el `FeedbackMessage` de Java** —
*instrumentación, no behavior change* — para que el runner pueda registrarlo en runs de
integración. Pendiente de decisión (ver §7).

## 4. Runner: `tools/run_experiments.py`

CLI:

```sh
python tools/run_experiments.py --experiment fear_response     # un experimento
python tools/run_experiments.py --all                           # todos
python tools/run_experiments.py --experiment fear_response --gui  # abre los PNG
```

Flujo:

```
experimento (JSON/YAML)
   ↓  stimulus script (light/distance/affectiveChange por ciclo)
   ↓  carga CognitiveOrchestrator REAL (LLM disabled)
   ↓  seed → bucle: perceive_and_update → heuristic_response → apply_feedback(scripted delta)
   ↓  CSV por ciclo + PNG
   ↓  results/<name>.{csv,png} + experiments/<name>_summary.md
```

## 5. Esquema de configuración por experimento

Cada experimento vive en `experiments/<name>.json` (o `.yaml`) y declara explícitamente:

```jsonc
{
  "name": "fear_response",
  "description": "low light + distant object, negative affective pressure",
  "llm": "disabled",            // forzar heurística (dinámica programada)
  "seed": 42,
  "initial_state": { "affective_valence": -0.20, "affective_momentum": 0.0 },
  "stimulus": {
    "light_level": ["Bajo", "Bajo", "Bajo", "Bajo", "Bajo", "Bajo", "Bajo"],
    "distance":     [3.2,  3.2,  3.0,  2.8,  3.5,  3.6,  3.8],
    "affective_change": [-0.12, -0.25, -0.30, -0.35, -0.40, -0.45, -0.48]  // "feedback" de Java
  },
  "cycles": 7
}
```

> `affective_change` simula la tabla de `CharacterBody.evaluateAffectiveFeedback`.
> No es una reimplementación del modelo afectivo; es el **estímulo de entrada** que el
> cuerpo real habría producido en esa situación.

## 6. Gráficas (`results/<name>.png`) — una figura por experimento

- **Figura 1** (eje izquierdo/derecho): `affective_valence` y `affective_momentum` vs `cycle`.
- **Figura 2**: `motor_output` y `sensor_sensitivity` vs `cycle` (paradoja emocional).
- **Figura 3 (opcional)**: timeline de `agent_state` / `action` por ciclo.

Lenguaje: `matplotlib` (única dependencia nueva, opcional; CSV siempre se genera).

## 7. Comparaciones (para demostrar sensibilidad al estado interno)

Mismo estímulo (`light=Bajo, distance=3.2`), distinto estado inicial:

- `normal affect` (valencia 0.10) → sensibilidad ~1.0, motor ~0.93
- `negative affect` (valencia −0.60) → sensibilidad ~1.3, motor ~0.72

Se grafican superpuestos en un mismo PNG → "lo mismo no produce lo mismo".

## 8. Layout de salida

```
experiments/
├── fear_response.md               # descripción humana
├── fear_response.json             # stimulus reproducible
├── exploration_response.md
├── exploration_response.json
├── habituation.md
├── habituation.json
├── affective_momentum.md
└── affective_momentum.json
results/
├── fear_response.csv
├── fear_response.png
├── exploration_response.csv
└── exploration_response.png
tools/
└── run_experiments.py
docs/
└── phase3_design.md               # este documento
```

## 9. Roadmap (sin features cognitivos nuevos)

- **Fase 3a:** runner + CSV (orquestador real en proceso, LLM disabled).
- **Fase 3b:** gráficas PNG (matplotlib) por experimento + comparaciones.
- **Fase 3c:** integración TCP real (Java+Python) parseando stdout para validar.
- **Fase 3d (opcional):** instrumentación mínima para exponer `saturation_factor`.

## 10. Decisiones pendientes (bloqueantes antes de implementar)

1. ¿ Aceptas el runner usando el `CognitiveOrchestrator` **real en proceso** (más fiable y
   reproducible) como la fuente de datos, y la integración TCP real solo como validación?
2. ¿ Quieres incluir `saturation_factor`? → implica la pequeña instrumentación en Java
   (señalado en §3). Sin ella, la columna quedará `null` en runs Python.
3. ¿ Generar gráficas con `matplotlib` (dependencia nueva) o limitarte a CSV + tabla ASCII en
   los `*_summary.md`?

## 11. Evidencia de validez (regla de oro)

- El runner **nunca** calcula `motor/sensitivity/valence` con sus propias fórmulas.
- Si `orchestrator.py` cambia su lógica, los resultados cambian automáticamente → la
  evidencia sigue siendo fiel.
- Todo cambio de instrumentación es **opt-in** y **flaggeado**, con el comportamiento
  por defecto idéntico al actual.