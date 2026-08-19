# 🧠 Hart Consciousness Model

> **Experimental embodied affective-cognitive architecture** — exploring affect, memory,
> perception and behavior through a **Java body**, a **Python affective orchestrator**
> and a local **Rust/GGUF cognitive agent**.

> ⚠️ **Nota científica:** este proyecto **no afirma implementar ni reproducir conciencia
> fenomenológica**. Explora mecanismos computacionales que pueden producir estados
> internos persistentes, percepción modulada por afecto, cognición y comportamiento.

---

## Propósito

Simulador cognitivo que integra **procesos separados** (cognitivo y encarnado) que se
comunican por **TCP/JSON** y modelan la interacción entre percepción, acciones y emoción.
El valor está en la **arquitectura** y en los **experimentos reproducibles** que la acompañan.

## Arquitectura

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
└────────┬─────────┘  JSON  └──────────┬───────────┘
         │                             │
         │ percepción                  ▼
    ┌───────────┐              ┌─────────────┐
    │  Entorno  │              │  Afecto     │
    │  simulado │              │  + memoria  │
    └───────────┘              └──────┬──────┘
                                      ▼
                            ┌─────────────────┐
                            │ motor + sensors │
                            └────────┬────────┘
                                     ▼
                                   JAVA
```

## Componentes

- **JAVA BODY — `java_body/`:** simula el cuerpo: percibe (luz, proximidad), ejecuta
  acciones y envía feedback afectivo. Su ritmo de ciclo se modula por el *motor*.
- **PYTHON ORCHESTRATOR — `orchestrator/`:** gestiona el estado afectivo (valencia), el
  *momentum* (inercia histórica), la habituación y la saturación conductual. Decide
  comandos y los modula con `motorOutput` (velocidad) y `sensorSensitivity`
  (amplitud de percepción).
- **RUST HART_AGENT — `hart_agent/`:** agente cognitivo con inferencia **GGUF real en
  CPU**. Separa **cerebro** (inferencia *event-driven*) y **cuerpo** (heartbeat ~60 Hz),
  y trata al LLM como componente **no confiable** (`fallback_response`, parseo JSON defensivo).

### La "paradoja emocional realista"

| Estado | Velocidad (motor) | Percepción (sensibilidad) |
|--------|-------------------|---------------------------|
| 🫣 Asustado | **Baja** (conserva energía) | **Alta** (hipervigilancia) |
| 😌 Confiado | **Alta** (explora) | **Baja** (no se distrae) |

Ciclo completo: **emoción → cognición → acción → percepción → emoción**.

## 📊 Experimentos

Dentro de [`experiments/`](experiments/) hay estudios reproducibles que demuestran
que las dinámicas programadas producen comportamientos **medibles y distintos**:

- [`fear_response.md`](experiments/fear_response.md) — valencia baja → *lento pero vigilante*
- [`exploration_response.md`](experiments/exploration_response.md) — valencia alta → *rápido, poco distraído*
- [`habituation.md`](experiments/habituation.md) — confort sostenido → aburrimiento → nueva acción
- [`affective_momentum.md`](experiments/affective_momentum.md) — inercia y decaimiento emocional

Cada experimento documenta **estímulo → parámetros del código → secuencia proyectada de
estados → comportamiento resultante → cómo reproducirlo**.

## 🛠️ Requisitos

- **Java 8+**
- **Python 3.10+**
- **Rust + Cargo** *(para `hart_agent`)*
- **Gson** — `lib/gson-2.13.1.jar`
- *(Opcional)* modelo **GGUF** (ver [`models/`](models/README.md)) para IA local

## 🚀 Cómo ejecutar

### Agente Java + orquestador Python

```sh
# terminal 1
cd java_body
javac -cp ".;..\lib\gson-2.13.1.jar" *.java
java -cp ".;..\lib\gson-2.13.1.jar" CharacterBody

# terminal 2
cd orchestrator
py orchestrator.py
```

O con un solo clic:

```sh
INIT_LIFE.bat
```

*(detecta puerto libre 5050–5100 y arranca ambos procesos).*

### Agente cognitivo Rust (opcional)

```sh
cd hart_agent
set HART_GGUF_PATH="C:\ruta\a\tu\modelo.gguf"
cargo run --release
```

## 🧩 Estructura del proyecto

```
├── java_body/        # Agente físico (Java): CharacterBody, CognitiveSocketBridge, ...
├── orchestrator/     # Orquestador cognitivo (Python): orchestrator.py
├── hart_agent/       # Agente cognitivo (Rust + GGUF)
├── models/           # Documentación de modelos GGUF (no subir archivos)
├── experiments/      # Experimentos reproducibles documentados
├── docs/             # Arquitectura y notas
│   ├── architecture.md
│   └── ARCHITECTURAL_NOTES.md
├── lib/gson-2.13.1.jar
├── INIT_LIFE.bat     # Lanzador Java + Python
├── INIT_LIFE2.bat    # Lanzador agente Rust (+ libclang/CMake)
├── BUILD_HART.bat    # Compila hart_agent
├── README.md
└── LICENSE
```

## 📚 Documentación

- [`docs/architecture.md`](docs/architecture.md) — componentes, cerebro/cuerpo y LLM no confiable.
- [`docs/ARCHITECTURAL_NOTES.md`](docs/ARCHITECTURAL_NOTES.md) — notas del modelo de conciencia y rutas de mejora.

## ⚠️ Notas técnicas

- **No subir** `hart_agent/target/`, `Modelo GGUF/` ni `*.class`: están en `.gitignore`.
- Los modelos GGUF son **grandes** → solo se documentan en [`models/`](models/README.md).

## 📄 Licencia

Distribuido bajo la licencia **MIT**. Consulta [`LICENSE`](LICENSE).