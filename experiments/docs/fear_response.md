# Experimento A — Respuesta al miedo (valencia baja)

**Objetivo:** verificar que estímulos negativos persistentes desplazan el estado afectivo
hacia el miedo y producen el patrón **"lento pero hipervigilante"**.

## Estímulo

Luz **baja** + objeto **distante** — entornos inciertos y percibidos como de riesgo.

## Mecánica del código (`orchestrator.py`)

```python
motor_output = clamp(0.3, 1.5, (0.9 + valencia*0.3) * (1.0 + momentum*0.2))
sensor_sensitivity:  val>0.5→0.8 | val>−0.3→1.0 | val>−0.7→1.3 | resto→1.8
                     (×1.2 si momentum < −0.2)
estados:  val>0.6 exploratory | >0.2 curious | >−0.2 neutral
          | >−0.5 cautious | >−0.8 seeking_safety | resto panic_avoidance
```

## Secuencia esperada (proyectada desde el código)

| Paso | Valencia | Estado | Sensibilidad | Motor |
|------|----------|--------|--------------|-------|
| inicio        | −0.20 | cautious         | 1.00 | 0.84 |
| tras estímulo  | −0.48 | cautious         | 1.30 | 0.76 |
| pérdida objeto | −0.67 | seeking_safety   | 1.30 | 0.70 |
| repetido       | −0.85 | panic_avoidance  | 1.80 | 0.64 |

## Comportamiento resultante

1. `observe` → movimiento cauto.
2. Sensibilidad alta + motor bajo: **escaneo atento pero desplazamiento lento**.
3. En pánico: máxima vigilancia (`1.8`) con motor mínimo (`0.64`).

## Cómo reproducir

```sh
# terminal 1 — en java_body/
java -cp ".;..\lib\gson-2.13.1.jar" CharacterBody
# terminal 2 — en orchestrator/
py orchestrator.py
```

Somete al agente a condiciones de luz baja con el objeto lejano y observa el descenso de
valencia en la salida `--- FEEDBACK AFECTIVO ---`.