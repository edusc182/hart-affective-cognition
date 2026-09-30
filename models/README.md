# Modelos GGUF

Los archivos de modelo **GGUF** no se suben al repositorio: son de varios gigabytes y superan
el límite de archivos de GitHub. En su lugar, este directorio documenta qué modelos se pueden
usar y cómo configurarlos.

## Configuración

El agente Rust (`hart_agent`) resuelve la ruta del modelo en este orden:

1. Variable de entorno `HART_GGUF_PATH`
2. Primer argumento al ejecutar `hart_agent`
3. `model.gguf` (por defecto) en el directorio de trabajo

### En Windows (cmd)

```sh
set HART_GGUF_PATH="C:\ruta\a\tu\modelo.gguf"
cd hart_agent
cargo run --release
```

O pasándolo por argumento:

```sh
cd hart_agent
cargo run --release -- "C:\ruta\a\tu\modelo.gguf"
```

## Modelos probados

| Modelo | Tamaño | Estado | Notas |
|--------|--------|--------|-------|
| MiniCPM-o-4.5 Q4_K_M | ~4 GB | **Presente localmente (no versionado)** | Es el `.gguf` que `INIT_LIFE2.bat` detecta en `Modelo GGUF\`. La inferencia extremo a extremo **no** se ha verificado en la última auditoría; lo único confirmado es que existe el binario de una build previa: `hart_agent/target/release/hart_agent.exe`. |

> Añade aquí cada modelo que **ejecutes de verdad**, indicando tamaño, idioma y resultado
> (si devuelve JSON estable, latencia, si dispara el `fallback_response`).
> No marques un modelo como "probado" sin haber visto una inferencia real completarse.

## Qué NO está verificado (estado actual)

- Que `hart_agent.exe` + el GGUF local completen una inferencia de principio a fin.
- Que la salida del modelo pase `extract_first_json_object` sin caer al `fallback_response`
  (ver [`docs/architecture.md`](../docs/architecture.md)).
- Cualquier medición de rendimiento (tok/s, RAM) en esta máquina.

## Recomendaciones

- Usa cuantizaciones **Q4_K_M / Q5_K_M** (buen equilibrio velocidad/calidad en CPU).
- Modelos *chat/instruct* responden mejor al formato del prompt en `hart_agent/src/main.rs`.
- Si el modelo no devuelve JSON válido, el sistema aplica un **fallback seguro** y sigue funcionando.