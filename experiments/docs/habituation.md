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

```bat
REM terminal 1 — en java_body\  (compila a classes\ y arranca el cuerpo)
javac -cp ..\lib\gson-2.13.1.jar -d classes *.java
java -cp ".;..\lib\gson-2.13.1.jar;classes" CharacterBody
REM terminal 2 — en orchestrator\
py orchestrator.py
```

Mantén luz `Alto` y distancia <0.5 m durante varios ciclos y observa el log:
`[COGNICION] Habituacion detectada: valencia ... -> ...`.

## Resultado medido (2026-09-30, commit `b7026f4`)

`python tools/run_experiments.py --experiment habituation --no-plots` (seed 99, LLM off):

| Ciclos | Valencia final | Momentum | Motor (1→8) | Sensibilidad | Estado final |
|--------|----------------|----------|-------------|--------------|--------------|
| 8 | +0.311 | +0.049 | 0.966 → 1.003 | 1.000 (constante) | `curious` |

En el **ciclo 6** se dispara la habituación (sexto ciclo cómodo): la acción pasa a
`Explorar el entorno buscando nuevos estimulos`, la valencia **baja** respecto al ciclo anterior
(0.3485 → 0.2374) y `repeat_count` se reinicia a 1. Fijado como regression test en
[`tests/test_regression_experiments.py`](../../tests/test_regression_experiments.py).