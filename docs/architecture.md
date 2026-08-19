# Arquitectura

Hart Consciousness Model separa procesos **cognitivos** y **encarnados (embodied)** que
se comunican mediante un puente **TCP/JSON** independiente del lenguaje.

## Diagrama general

```text
┌──────────────────────┐
│      GGUF / LLM      │
│    Rust / llama.cpp  │
└──────────┬───────────┘
           │
      COGNICIÓN
           │
           ▼
┌──────────────────┐        ┌──────────────────────┐
│   JAVA BODY      │  TCP   │  PYTHON ORCHESTRATOR │
│                  │◄──────►│                      │
│   java_body/     │  JSON  │   orchestrator/      │
└────────┬─────────┘        └──────────┬───────────┘
         │                            │
         │ percepción                 │
         │                            ▼
    ┌───────────┐               ┌─────────────┐
    │  Entorno  │               │  Afecto     │
    │ simulado  │               │  + memoria  │
    └───────────┘               └──────┬──────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ motor + sensors │
                              └────────┬────────┘
                                       │
                                       ▼
                                    JAVA
```

## Componentes

### 1. Java BODY — `java_body/`
Simula el cuerpo físico: percibe (luz, proximidad), ejecuta acciones y envía feedback
afectivo. Su ritmo de ciclo se modula por el **motor** calculado en cognición.

### 2. Python ORCHESTRATOR — `orchestrator/`
Gestiona el estado afectivo (valencia), el *momentum* (inercia histórica), la habituación
(`apply_boredom_drive`) y la saturación conductual. Decide comandos y los modula con
`motorOutput` y `sensorSensitivity`.

### 3. Rust HART_AGENT — `hart_agent/`
Agente cognitivo con inferencia GGUF **real en CPU**. Separa explícitamente **cerebro** y **cuerpo**.

## Cerebro / Cuerpo en Rust

```text
CEREBRO                        CUERPO
inferencia GGUF                heartbeat ~60 Hz
  ↓                            estado (valencia, tensión)
  canal crossbeam              percepción autónoma
  RespuestaCognitiva (JSON)    ↓→ cerebro
```

- **Inferencia cognitiva:** *event-driven*, tasa variable (solo cuando llega una percepción).
- **Heartbeat del cuerpo:** ~60 Hz, mantiene el estado y el latido.

No es necesario que un LLM "piense" 60 veces por segundo: la **separación de tasas**
(cuerpo rápido / cerebro lento) es intencional y realista.

## El LLM como componente no confiable

Pedir JSON a un LLM no garantiza JSON válido. El agente Rust trata el modelo como un
componente **no confiable**:

- `normalize_model_output` — limpia markdown / cierres de turno.
- `extract_first_json_object` — extrae el primer objeto `{...}` balanceado.
- `maybe_wrap_json_body` — repara cuerpos JSON truncados (falta la llave de apertura).
- `fallback_response` — respuesta segura si el modelo no devuelve JSON aprovechable.

Esto permite que la simulación siga funcionando incluso cuando el modelo "delira".

## Gramática del afecto

Ciclo completo: **emoción → cognición → acción → percepción → emoción**.
El estado emocional modula el **tempo** del proceso (la "paradoja realista"):
un agente asustado es **lento pero hipervigilante**; uno confiado, **rápido pero distraído**.