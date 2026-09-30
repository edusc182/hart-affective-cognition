# Experimento D — Momentum afectivo (inercia)

**Objetivo:** mostrar que un solo estímulo fuerte **no** revierte de inmediato una
tendencia afectiva: hay **inercia** que suaviza los cambios (resiliencia temporal).

## Mecánica del código (`orchestrator.py`)

```python
# Inercia: media ponderada (mayor peso al más reciente) de los últimos <=4 cambios
def compute_historical_inertia(self):
    # delta reciente más antiguo tiene peso 1, el más reciente peso n (hasta 4)
    weighted_total += delta * index ; weight_sum += index
    return weighted_total / weight_sum

# Mezcla del impulso directo con la inercia histórica
def blend_affective_delta(self, direct_delta):
    effective = 0.6 * direct_delta + 0.4 * historical_inertia

# Decaimiento temporal: la valencia tiende a 0 antes de sumar el nuevo impulso
decayed = valencia * self.affective_decayRate   # decayRate = 0.95
new_valence = clamp(-1.0, 1.0, decayed + effective)
```

## Comportamiento demostrable

1. **Saturación emocional**: dos impulsos en la misma dirección se acumulan pero son
   modulados por `affective_alpha = 0.6` (impulso directo) frente a `0.4` (inercia).
2. **Decaimiento**: en cada ciclo la valencia se multiplica por `0.95` → la emoción
   *desaparece* gradualmente si no se refuerza.
3. **Atenuación saludable**: un único pico de miedo positivo/negativo genera un cambio
   inmediato, pero **no** un estado permanente (requiere refuerzo sostenido).

## Ejemplo ilustrativo (proyección)

| Ciclo | Impulso directo | Valencia antes | Inercia | Valencia después |
|-------|-----------------|----------------|---------|------------------|
| 1 | +0.30 | 0.10 | 0.00 | +0.22 |
| 2 | +0.10 | 0.22 | +0.30 | +0.29 |
| 3 | +0.00 | 0.29 | +0.22 | +0.27 |

> El pico (`+0.30`) **no** colapsa a cero: la inercia histórica +0.22 sostiene
> parcialmente el estado, y el decaimiento lo erosiona solo si deja de reforzarse.

## Conclusión

El momentum produce **resiliencia**: las transiciones emocionales son **temporales** y
**acumulativas**, requisito para que la simulación parezca "viva" en vez de binaria
(feliz ↔ triste), y para que el motor/sensibilidad respondan de forma gradual y medible.

## Cómo reproducir

```bat
REM terminal 1 — en java_body\  (compila a classes\ y arranca el cuerpo)
javac -cp ..\lib\gson-2.13.1.jar -d classes *.java
java -cp ".;..\lib\gson-2.13.1.jar;classes" CharacterBody
REM terminal 2 — en orchestrator\
py orchestrator.py
```

Alimenta impulsos alternados y observa `-- FEEDBACK AFECTIVO --`: fíjate en los campos
`DeltaAct`, `Inercia` y `DeltaTotal` y en cómo `Valencia` nunca salta de golpe.

## Resultado medido (2026-09-30, commit `b7026f4`)

`python tools/run_experiments.py --experiment affective_momentum --no-plots` (seed 21, LLM off):

| Ciclos | Valencia final | Momentum | Motor (1→6) | Sensibilidad | Estado final |
|--------|----------------|----------|-------------|--------------|--------------|
| 6 | +0.060 | −0.052 | 0.954 → 0.909 | 1.000 (constante) | `neutral` |

Trayectoria del momentum (impulsos `+0.30, 0, 0, −0.30, 0, 0`):
`0.000 → +0.180 → +0.108 → +0.076 → −0.049 → −0.052`, es decir **inercia que decae** cuando deja de
haber refuerzo. Fijado como regression test en
[`tests/test_regression_experiments.py`](../../tests/test_regression_experiments.py).