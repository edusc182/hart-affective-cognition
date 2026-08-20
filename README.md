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

- [`fear_response.md`](experiments/docs/fear_response.md) — valencia baja → *lento pero vigilante*
- [`exploration_response.md`](experiments/docs/exploration_response.md) — valencia alta → *rápido, poco distraído*
- [`habituation.md`](experiments/docs/habituation.md) — confort sostenido → aburrimiento → nueva acción
- [`affective_momentum.md`](experiments/docs/affective_momentum.md) — inercia y decaimiento emocional

Cada experimento documenta **estímulo → parámetros del código → secuencia proyectada de
estados → comportamiento resultante → cómo reproducirlo**.

## 🛠️ Requisitos

| Componente | Requisito |
|-----------|-----------|
| **Runner de experimentos** (recomendado) | **Python 3.10+** (solo stdlib) |
| **Agente físico (Java)** | **Java 8+** + [Gson](https://github.com/google/gson) |
| **Agente cognitivo (Rust)** | **Rust + Cargo** *(opcional)* |
| **IA local (GGUF)** | *Opcional* — ver [`models/`](models/README.md) |

El `.jar` de Gson ya viene incluido en `lib/gson-2.13.1.jar`. El núcleo de
Python usa la biblioteca estándar; `matplotlib` y `llama-cpp-python` son
**opcionales** (ver [`requirements.txt`](requirements.txt)).

## 🚀 Cómo ejecutar

### Opción A — Windows (doble clic)

```sh
INIT_LIFE.bat     # compila Java y arranca Java + Python (puerto libre 5050–5100)
INIT_LIFE2.bat    # además lanza el agente Rust (si tienes un modelo GGUF)
```

### Opción B — Linux / macOS (consola)

```bash
./setup.sh        # compila java_body y crea .venv/ (una vez)
```

Después, en dos terminales:

```sh
# Terminal 1 — cuerpo Java
cd java_body
javac -cp ".:../lib/gson-2.13.1.jar" -d classes *.java
java -cp ".:../lib/gson-2.13.1.jar:classes" CharacterBody 5050

# Terminal 2 — orquestador cognitivo
cd ../orchestrator
python orchestrator.py --port 5050
```

> Nota: en Windows el separador de classpath es `;` ; en Linux/macOS es `:`.
> Alternativa sin ventanas: `setup.sh` + Docker (abajo).

### Opción C — Docker (reproducible, headless)

```bash
docker build -f Dockerfile -t hart-console .
docker run --rm hart-console                      # reproduce TODOS los experiments
docker run --rm hart-console --experiment fear_response
```

### Reproducir los experimentos (sin Java ni Rust)

El runner mide el orquestador **real** (no lo reimplementa) y deja CSV + summary en
`experiments/results/`:

```sh
python3 tools/run_experiments.py --all                 # todos, con gráficas
python3 tools/run_experiments.py --experiment habituation --no-plots
```

### Agente cognitivo Rust (opcional, IA local)

```sh
cd hart_agent
set HART_GGUF_PATH="C:\ruta\a\tu\modelo.gguf"  # Linux: export HART_GGUF_PATH=...
cargo run --release
```

## 📡 Telemetría del cuerpo (opcional)

El feedback de Java incluye `saturationFactor`, `repeatCount` y `switchRate`
(saturación conductual por repetición y persistencia temporal). Se exponen siempre
en el JSON de feedback; para además emitir una línea aislada por ciclo, arranca el
JVM con el flag:

```bash
java -DHART_TELEMETRY=true -cp ".:../lib/gson-2.13.1.jar:classes" CharacterBody
```

## 🧩 Estructura del proyecto

```text
├── java_body/          # Agente físico (Java): CharacterBody, CognitiveSocketBridge, ...
├── orchestrator/       # Orquestador cognitivo (Python): orchestrator.py
├── hart_agent/         # Agente cognitivo (Rust + GGUF)
├── tools/              # Runner reproducible de experiments (run_experiments.py)
├── models/             # Documentación de modelos GGUF (no subir archivos)
├── experiments/
│   ├── configs/        # Estímulos reproducibles (JSON)
│   ├── docs/           # Informes de cada experimento (MD)
│   └── results/        # CSV + PNG generados localmente (ignorado por git)
├── docs/               # Arquitectura y notas
│   ├── architecture.md
│   └── ARCHITECTURAL_NOTES.md
├── lib/gson-2.13.1.jar
├── INIT_LIFE.bat       # Lanzador Java + Python (Windows)
├── INIT_LIFE2.bat      # Lanzador agente Rust (+ libclang/CMake)
├── BUILD_HART.bat      # Compila hart_agent
├── setup.sh            # Preparación Linux/macOS
├── Dockerfile          # Entorno headless reproducible (experimentos)
├── requirements.txt    # Dependencias Python opcionales
├── .gitattributes      # Normalización de fin de línea
├── .dockerignore
├── CONTRIBUTING.md
├── README.md
└── LICENSE
```

## 📚 Documentación

- [`docs/architecture.md`](docs/architecture.md) — componentes, cerebro/cuerpo y LLM no confiable.
- [`docs/ARCHITECTURAL_NOTES.md`](docs/ARCHITECTURAL_NOTES.md) — notas del modelo de conciencia y rutas de mejora.

## ⚠️ Notas técnicas

- **No subir** `hart_agent/target/`, `Modelo GGUF/` ni `*.class`: están en `.gitignore`.
- Los modelos GGUF son **grandes** → solo se documentan en [`models/`](models/README.md).

## 🚀 Roadmap / Ideas

- **Portátil total**: CI en GitHub Actions que compile Java (`javac`), Rust (`cargo build`) y
  ejecute `tools/run_experiments.py --all` para validar que los CSVs siguen siendo estables.
- **Versión GUI**: `SimulationWindow` (Java) ya existe; mejorarlo como visualizador del estado.
- **Más experimentos**: cualquier dinámica afectiva nueva merece un `experiments/configs/*.json`.
- **Servidor de telemetría**: `AffectiveTelemetryUDP` puede alimentar dashboards en vivo.

## 🤝 Contribuir

Lee **[`CONTRIBUTING.md`](CONTRIBUTING.md)**: cómo probar, convenciones de commit
(inglés, imperativo) y las reglas de oro (medir el sistema real, no reescribirlo;
telemetría opt-in; no subir binarios/GGUF).

## 📄 Licencia

Distribuido bajo la licencia **MIT**. Consulta [`LICENSE`](LICENSE).