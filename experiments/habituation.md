# Experimento C — Habituación (aburrimiento)

**Objetivo:** demostrar que un entorno **estable y cómodo** termina generando
aburrimiento, y que esto impulsa al agente a **buscar nuevos estímulos**.

## Estímulo

Mismo entorno: **luz alta + objeto muy cerca (<0.5 m)** de forma sostenida.
La zona de confort es reconfortante al principio, pero se vuelve estancamiento.

## Mecánica del código (`orchestrator.py`)

```python
def apply_boredom_drive(self, thought, action):
    if light_level == "Alto" and distance < 0.5:
        self.cycles_in_comfort += 1
    else:
        self.cycles_in_comfort = 0

    if self.cycles_in_comfort > 5:            # 6+ ciclos cómodos
        old = self.state["affective_valence"]
        self.state["affective_valence"] = clamp(old - 0.15)
        self.cycles_in_comfort = 0
        boredom_action = "Explorar el entorno buscando nuevos estimulos"
```

## Secuencia esperada

| Ciclos cómodos | Valencia | Estado | Acción |
|----------------|----------|--------|--------|
| 0–5        | estable | neutral  | mantener postura |
| 6          | −0.15   | (baja)   | **explorar** |
| …          | trend ↓ | cautious | búsqueda activa |

## Comportamiento resultante

1. El confort sostenido **reduce la valencia** (−0.15 por evento).
2. El agente **rompe la fijación** y emite una nueva acción exploratoria.
3. Solo se produce con **6+ ciclos** de comodidad → es *habituación*, no ruido.

## Cómo reproducir

```sh
# terminal 1 — en java_body/
java -cp ".;..\lib\gson-2.13.1.jar" CharacterBody
# terminal 2 — en orchestrator/
py orchestrator.py
```

Mantén luz `Alto` y distancia <0.5 m durante varios ciclos y observa el log:
`[COGNICION] Habituacion detectada: valencia ... -> ...`.