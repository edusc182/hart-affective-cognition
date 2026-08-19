# 🧠 Hart Consciousness Model (Simu2)

Simulación cognitiva que integra un **agente físico (Java)**, un **orquestador cognitivo (Python)** y un **agente con IA local (Rust + GGUF)** para modelar comportamiento, emociones y retroalimentación afectiva en tiempo real.

El sistema experimenta con la interacción entre **percepción sensorial**, **acciones físicas** y **estados emocionales**, comunicándose mediante un protocolo robusto **TCP / JSON**.

---

## ✨ ¿Qué hace?

- **Java (`CharacterBody.java`):** simula el cuerpo físico del agente. Recibe comandos, ejecuta acciones, percibe el entorno (nivel de luz, proximidad a objetos) y envía feedback emocional.
- **Python (`orchestrator.py`):** orquesta la cognición: gestiona el estado afectivo (valencia), el decaimiento emocional, el *momentum*, la saturación conductual y la reconexión automática.
- **Rust (`hart_agent/`):** agente cognitivo opcional con **inferencia GGUF real por CPU** (modelo de lenguaje local).
- **Comunicación:** ambos procesos se comunican por **TCP** usando mensajes **JSON**.

### La "paradoja emocional realista"

Una de las ideas centrales del modelo: el estado emocional modula el *tempo* del ciclo de procesamiento.

| Estado | Velocidad de procesamiento | Percepción sensorial |
|--------|----------------------------|----------------------|
| 🫣 Asustado | **Lenta** (analiza amenazas) | **Alta** (hipervigilancia) |
| 😌 Confiado | **Rápida** (explora) | **Baja** (atención relajada) |

Ciclo completo: **emoción → cognición → acción → percepción → emoción**.

---

## 🛠️ Requisitos previos

- **Java 8+** (compilar y ejecutar `CharacterBody.java`)
- **Python 3.10+** (recomendado 3.13)
- **Rust + Cargo** (para `hart_agent`)
- *(Opcional)* `llama_cpp` para IA avanzada en Python, o un modelo GGUF para Rust
- **Gson** (`lib/gson-2.13.1.jar`) para el agente Java

---

## 🚀 Cómo ejecutar

### 1. Compilar el agente Java

```sh
javac -cp ".;lib\gson-2.13.1.jar" CharacterBody.java CognitiveSocketBridge.java SensoryData.java FeedbackData.java
```

### 2. Ejecutar el agente Java

```sh
java -cp ".;lib\gson-2.13.1.jar" CharacterBody
```

Verás: `[BODY INIT] Cuerpo fisico instanciado y listo para recibir comandos.`

### 3. Ejecutar el orquestador cognitivo (Python)

```sh
py orchestrator.py
```

O con modelo GGUF opcional:

```sh
py orchestrator.py --model-path "C:\ruta\a\modelo.gguf"
```

> 💡 Si aparece `WinError 10061`, el agente Java no está escuchando; asegúrate de que la terminal de Java siga abierta y vuelve a ejecutar Python.

### 4. Inicio automático (doble clic)

```sh
INIT_LIFE.bat
```

Compila Java, detecta un puerto libre entre 5050–5100 e inicia Java y Python con el mismo puerto para evitar conflictos.

### 5. Agente Rust con inferencia GGUF (opcional)

```sh
cd hart_agent
set HART_GGUF_PATH="C:\ruta\a\tu\modelo.gguf"
cargo run --release
```

O pasando el modelo por argumento:

```sh
cargo run --release -- "C:\ruta\a\tu\modelo.gguf"
```

> Carga el modelo GGUF en CPU, lanza un hilo de cerebro (inferencia) y un hilo de cuerpo (latido a 60 Hz). Si el modelo no responde JSON válido, se aplica un fallback cognitivo seguro.

---

## 🧩 Estructura del proyecto

```
├── CharacterBody.java        # Agente físico (Java)
├── CognitiveSocketBridge.java# Puente de comunicación TCP/JSON
├── SensoryData.java          # Datos sensoriales
├── FeedbackData.java         # Datos de feedback afectivo
├── orchestrator.py          # Orquestador cognitivo (Python)
├── hart_agent/               # Agente cognitivo (Rust + GGUF)
├── lib/gson-2.13.1.jar       # Dependencia Gson
├── INIT_LIFE.bat             # Lanzador Java + Python
└── INIT_LIFE2.bat            # Lanzador agente Rust
```

---

## 🔬 ¿Para qué sirve?

- **Investigación en cognición artificial y emociones.**
- **Simulación de agentes autónomos con feedback emocional.**
- **Experimentación con protocolos robustos de comunicación entre lenguajes** (Java ↔ Python ↔ Rust).
- **Base para sistemas de IA encarnada, robótica o videojuegos con emociones realistas.**

---

## 📚 Documentación adicional

- [`ARCHITECTURAL_NOTES.md`](ARCHITECTURAL_NOTES.md) — notas sobre la arquitectura, el modelo de conciencia y rutas de mejora (p. ej. flujo bidireccional de la valencia afectiva hacia las decisiones de Java).

---

## ⚠️ Solución de problemas comunes

### `package com.google.gson does not exist`
Falta Gson en el classpath. Verifica que exista `lib\gson-2.13.1.jar` y usa los comandos de compilación de arriba.

### Rust: `Unable to find libclang (clang.dll / libclang.dll)`
Falta LLVM/Clang (requerido por `bindgen` en `llama-cpp-sys-2`).

1. Instala LLVM desde <https://releases.llvm.org/download.html>.
2. Verifica `C:\Program Files\LLVM\bin\libclang.dll`.
3. En la terminal de compilación:

```sh
set "LIBCLANG_PATH=C:\Program Files\LLVM\bin"
set "PATH=%LIBCLANG_PATH%;%PATH%"
```

4. Reintenta:

```sh
cargo clean
cargo run --release -- "C:\ruta\a\tu\modelo.gguf"
```

---

## 📄 Licencia

Este proyecto se distribuye bajo la licencia **MIT**. Consulta el archivo [`LICENSE`](LICENSE).
