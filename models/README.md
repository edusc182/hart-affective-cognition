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

> Aquí puedes listar los modelos GGUF que has comprobado, indicando tamaño, idioma y resultado.

| Modelo | Tamaño | Notas |
|--------|--------|-------|
| *(ejemplo)* Gemma-4-E4B-Uncensored Q4_K_M | ~4 GB | Funciona en CPU; respuestas JSON estables |

## Recomendaciones

- Usa cuantizaciones **Q4_K_M / Q5_K_M** (buen equilibrio velocidad/calidad en CPU).
- Modelos *chat/instruct* responden mejor al formato del prompt en `hart_agent/src/main.rs`.
- Si el modelo no devuelve JSON válido, el sistema aplica un **fallback seguro** y sigue funcionando.