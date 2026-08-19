# Experimento B — Exploración (valencia alta)

**Objetivo:** verificar el patrón inverso al miedo: **rápido pero con atención reducida**,
o sea exploración activa y confiada.

## Estímulo

Entorno **brillante** + objeto **cercano** — percibido como conspicuo y abordable.

## Mecánica del código (`orchestrator.py`)

```python
# valencia +0.10 → +0.40 → +0.67
motor = (0.9 + val*0.3) * (1 + momentum*0.2)   # 0.93 → 1.02 → 1.10
sensibilidad: val>0.5 → 0.8 | val>−0.3 → 1.0   # 1.00 → 1.00 → 0.80
estados: curiosidad moderada → `curious` → `exploratory`
```

## Secuencia esperada (proyectada desde el código)

| Paso | Valencia | Estado | Sensibilidad | Motor |
|------|----------|--------|--------------|-------|
| inicio       | +0.10 | neutral      | 1.00 | 0.93 |
| acercamiento | +0.40 | curious      | 1.00 | 1.02 |
| contacto     | +0.67 | exploratory  | 0.80 | 1.10 |

## Comportamiento resultante

1. `observe` → curiosidad moderada (`curious`).
2. Al confirmar que es seguro: **exploración activa** (`exploratory`).
3. Sensibilidad baja (`0.80`): el agente **no se distrae** y avanza rápido (`1.10`).

Comparado con el Experimento A, el **mismo estímulo** navega el espacio de estado en la
dirección opuesta: la valencia positiva **acelera el motor** y **reduce la vigilancia**.

## Cómo reproducir

```sh
# terminal 1 — en java_body/
java -cp ".;..\lib\gson-2.13.1.jar" CharacterBody
# terminal 2 — en orchestrator/
py orchestrator.py
```

Presenta al agente un entorno con luz alta y el objeto cerca, y observa el ascenso de
valencia y el paso `neutral → curious → exploratory`.