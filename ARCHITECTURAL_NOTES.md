# Notas Arquitectónicas: Simu2 Hart Consciousness Model

## Estado Actual del Sistema

### Flujo Unidireccional (Incompleto)
```
Java (CharacterBody)
    ↓ sendFeedback(action, affectiveChange)
    ↓ [lightLevel, proximity, action, affectiveChange]
    
Python (Orchestrator)
    ↓ recibe feedback y actualiza: affective_valence, affective_momentum
    ↓ calcula decisión
    ↓ sendCommand(command)
    
Java (CharacterBody)
    ↓ recibe comando
    ↓ ejecuta acción (SIN usar valence del agente)
```

**Problema:** La `affective_valence` calculada en Python se queda en Python y **nunca influye en las decisiones de Java**.

---

## Observación Técnica

En CharacterBody.java, la heurística de decisión (`decideFallbackCommand`) está **hardcodeada** y no depende del estado emocional:

```java
if ("Alto".equals(perception.getLightLevel()) 
        && perception.getProximityToObjectMeters() < 1.0) {
    return "Examinar objeto rojo con curiosidad intensa"; // Siempre igual
}
```

No importa si el agente está ansioso (valence -0.8) o feliz (valence +0.8): sigue con la misma acción.

---

## Propuesta de Mejora: Flujo Bidireccional

### 1. Extender Protocolo JSON

**Respuesta de Python (CommandResponse mejorada):**
```json
{
  "type": "command",
  "sequence": 42,
  "command": "Examinar objeto rojo",
  "affective_valence": 0.13,
  "affective_momentum": -0.05,
  "agent_state": "exploratory|cautious|seeking_safety"
}
```

### 2. Modificar CharacterBody para usar Valencia

En `decideFallbackCommand`, modular decisiones basadas en valence:

```java
// Con valence bajo: buscar seguridad
if (agentValence < -0.5) {
    // Exploración agresiva de seguridad, no solo caminar lentamente
    return "Buscar entorno seguro con cautela elevada";
}

// Con valence alto: exploración activa
if (agentValence > 0.5) {
    return "Explorar territorio desconocido";
}
```

### 3. Impacto en Saturación Conductual

Con la Valencia, refinar `computeSaturationFactor`:

```java
// Si valence es bajo (ansioso), la repetición es aún más saturante
// porque refleja fijación ansiosa, no exploración
if (agentValence < -0.3 && repeatCount > 1) {
    // Penalizar más la repetición
    double anxietySaturation = 0.1; // más severa
}
```

---

## Beneficios de la Arquitectura Bidireccional

1. **Congruencia Emocional:** El agente actúa congruente con su estado emocional interno.
2. **Exploración Dinámica:** Con valence bajo, busca seguridad; con valence alto, explora agresivamente.
3. **Realismo Comportamental:** Un agente ansioso NO explora igual que uno tranquilo.
4. **Feedback Circular:** Acciones → cambio emocional → nuevas acciones → cambio emocional (ciclo realista).

---

## Pasos de Implementación

1. **Fase 1 (Próxima):** Extender `CommandResponse` en Java para incluir valence y agent_state.
2. **Fase 2:** Modificar Python para enviar valence en cada comando.
3. **Fase 3:** Actualizar `decideFallbackCommand` para usar valence en heurísticas.
4. **Fase 4:** Refinar saturación conductual con factor de ansiedad.

---

## Observación Técnica del Usuario

> "¿Has notado si la Valencia está afectando la velocidad de procesamiento o la toma de decisiones en el lado de Java?"

**Respuesta:** No, actualmente **no está afectando nada en Java**. Es solo logging y estado interno en Python. Este es el siguiente refinamiento arquitectónico crítico para lograr una verdadera "conciencia contextualizada y resiliente".

---

## Implementación: Arquitectura Bidireccional (Opción B) ✓ COMPLETADA

### Cambios Realizados

#### 1. Extensión del Protocolo (CognitiveSocketBridge.java)

`BridgeCommand` ahora incluye:
```java
class BridgeCommand {
    String command;              // Acción a ejecutar
    double affectiveValence;     // Valencia del agente (-1.0 a +1.0)
    double affectiveMomentum;    // Inercia afectiva
    String agentState;           // Estado descriptivo: exploratory|curious|neutral|cautious|seeking_safety|panic_avoidance
}
```

#### 2. Modulación de Acciones en Java (CharacterBody.decideFallbackCommand)

La heurística ahora depende de Valencia:

```java
if ("Alto" equals light) && proximity < 1.0) {
    if (valence > 0.5) {
        return "Explorar con confianza y curiosidad extrema";       // Arriesgado
    } else if (valence < -0.3) {
        return "Examinar objeto rojo con cautela defensiva";        // Defensivo
    } else {
        return "Examinar objeto rojo con curiosidad intensa";       // Normal
    }
}
```

**Beneficio:** El agente actúa congruente con su estado emocional.

#### 3. Modulación de Percepción en Java (CharacterBody.getSensoryInput)

Gating sensorial adaptativo (Túnel de Atención):

```java
double perceptionModifier = 1.0 + (valence * 0.3); // rango: 0.85 a 1.3

// Objetos cercanos (simulatedProximity *= perceptionModifier)
// Alta curiosidad: FOV expandido, objetos parecen más cercanos (detección + sensitiva)
// Alta ansiedad: FOV restrictivo, objetos parecen más lejanos (foco estrecho)
```

**Beneficio:** Comportamiento realista: agentes ansiosos tienen "túnel de atención", agentes curiosos "escanean" más.

#### 4. Cálculo de Agent State en Python (compute_agent_state)

```python
def compute_agent_state(self):
    if valence > 0.6: return "exploratory"
    if valence > 0.2: return "curious"
    if valence > -0.2: return "neutral"
    if valence > -0.5: return "cautious"
    if valence > -0.8: return "seeking_safety"
    return "panic_avoidance"
```

#### 5. Envío de Estado Afectivo en Comandos (Untitled-1.py)

```python
response = {
    "type": "command",
    "command": desired_action,
    "affectiveValence": orchestrator.state["affective_valence"],
    "affectiveMomentum": orchestrator.state["affective_momentum"],
    "agentState": agent_state
}
```

---

## Flujo Completo: Antes vs. Después

### ANTES (Unidireccional - Incompleto)
```
Java Percepciones
    ↓
    ↓ sendFeedback(action, affectiveChange)
    ↓
Python actualiza affective_valence
    ↓
    ↓ sendCommand(command) [sin enviar valence]
    ↓
Java ejecuta comando IGNORANDO valencia (hardcoded heuristic)
```

### DESPUÉS (Bidireccional - Completo)
```
Java Percepciones (moduladas por valencia anterior)
    ↓
    ↓ sendFeedback(action, affectiveChange)
    ↓
Python actualiza affective_valence + calcula agentState
    ↓
    ↓ sendCommand(command, valence, agentState)
    ↓
Java recibe valence → decide acciones moduladas → modula próxima percepción
    ↓ [Ciclo cerrado, congruencia emocional]
```

---

## Impacto Behavioral

### Ejemplo: Agente en Oscuridad Cercana

**Escenario:** Luz baja, objeto a 0.5 metros

**Caso 1: Valencia +0.7 (Exploratorio)**
- `decideFallbackCommand()` retorna: "Explorar territorio desconocido"
- `getSensoryInput()` expande FOV: objetos percibidos más lejanos (curiosidad)
- Comportamiento: Avanza agresivamente, explora con confianza

**Caso 2: Valencia -0.8 (Pánico)**
- `decideFallbackCommand()` retorna: "Mantener posicion actual y evaluar amenazas"
- `getSensoryInput()` restringe FOV: túnel de atención, objetos parecen más cercanos
- Comportamiento: Se paraliza, no explora, foco en amenaza inmediata

**Ambos perciben LO MISMO**, pero reaccionan DIFERENTE basado en su estado emocional. 

→ **Esto es agencia verdadera, no solo logging.**

---

## Próximos Refinamientos (Opcionales)

1. **Saturación con Factor de Ansiedad:** Si `valence < -0.3` y `repeatCount > 1`, aplicar penalización más severa (fijación ansiosa).
2. **Feedback Somático:** Modular velocidad de sleep() en main loop basado en ansiedad (agentes ansiosos procesan más rápido).
3. **Olvido Emocional:** Cuando valence es muy negativo, purgar memoria de eventos positivos (sesgo de interpretación).

---

## Conclusion

La arquitectura bidireccional cierra el círculo: **emoción → percepción → acción → nuevaemoción**. El agente ya no es un observador desapegado; es un sistema embodied donde lo afectivo determina lo comportamental.

Esto es "conciencia contextualizada y resiliente": el mismo entorno objetivo produce comportamientos cualitativamente diferentes según el estado interno del agente.

---

# Resiliencia del Agente: Moduladores Dinámicos

## Problema: Colapso Conductual

En la arquitectura bidireccional pura, si el objeto rojo desaparece o la luz cae drásticamente, la Valencia colapsará, modulando acciones y percepción. Pero **no hay ningún mecanismo que ralentice el procesamiento mismo del agente**, lo que puede llevar a:
- Ciclos de percepción tan rápidos que el agente "se desmorona" emocionalmente en tiempo real.
- Decisiones reactivas sin tiempo para recuperación.
- Falta de "inercia temporal" que es característica de seres conscientes reales.

## Solución: Motor Output y Sensor Sensitivity Dinámicos

Implementamos dos **moduladores de resiliencia** que permiten que Python regule el **ritmo temporal** del agente Java:

### 1. Motor Output (Velocidad de Ejecución)

**Rango:** 0.3 (paralizado) a 1.5 (hiperkinético)  
**Fórmula en Python:**
```python
base_motor = 0.9 + (valence * 0.3)  # -1.0 → 0.6, +1.0 → 1.2
momentum_modifier = 1.0 + (momentum * 0.2)
motor_output = base_motor * momentum_modifier
```

**Aplicación en Java:**
```java
long adjustedDelay = (long) ((baseDelay + variableDelay) / motor);
Thread.sleep(adjustedDelay);
```

**Efecto:**
- **Valencia baja (-0.8):** motor ≈ 0.66 → delay ≈ 850ms (muy lento, conservador)
- **Valencia neutra (0.0):** motor ≈ 1.0 → delay ≈ 550ms (normal)
- **Valencia alta (+0.7):** motor ≈ 1.3 → delay ≈ 425ms (rápido, exploratorio)

**Realismo:** Un agente asustado se mueve **lentamente** porque está usando energía para evaluar amenazas. Un agente confiado se mueve rápido porque explora con seguridad.

### 2. Sensor Sensitivity (Amplitud Atencional)

**Rango:** 0.5 (túnel extremo) a 1.8 (hipervigilancia)  
**Fórmula en Python:**
```python
if valence > 0.5: base_sensitivity = 0.8  # Confiado: reduce ruido
elif valence > -0.3: base_sensitivity = 1.0  # Neutral
elif valence > -0.7: base_sensitivity = 1.3  # Cauteloso: amplifica alertas
else: base_sensitivity = 1.8  # Pánico: máxima hipervigilancia

if momentum < -0.2: base_sensitivity *= 1.2  # Deterioro → aumenta urgencia
```

**Aplicación en Java:**
```java
double perceptionModifier = (1.0 + (valence * 0.3)) * sensorSensitivity.get();
// Aplicado en getSensoryInput() para modular FOV
```

**Efecto:**
- **Valencia baja + momentum negativo:** sensitivity ≈ 2.16 → FOV muy expandido (hipervigilancia)
- **Valencia neutra:** sensitivity ≈ 1.0 → FOV normal
- **Valencia alta:** sensitivity ≈ 0.8 → FOV restrictivo (confianza, menos distracción)

**Realismo:** Un agente asustado tiene **"túnel de atención"** paradójico: se mueve lentamente (motor bajo) pero percibe MÁS cosas (sensibilidad alta) porque busca amenazas. Un agente confiado es lo opuesto.

## Flujo Completo de Resiliencia

```
Percepción Java (modulada por sensorSensitivity anterior)
    ↓
Feedback a Python: "El objeto desapareció"
    ↓
Python: Valencia collapsa de 0.5 → -0.7 (pánico)
    ↓
Python calcula:
    - motorOutput = 0.6 (muy lento)
    - sensorSensitivity = 1.8 (máxima alerta)
    ↓
Envía comando a Java CON moduladores
    ↓
Java recibe: "Mantener posicion actual | motor=0.6, sensor=1.8"
    ↓
Java aplica:
    - sleep(adjustedDelay / 0.6) = MUCHO MÁS TIEMPO entre ciclos
    - perceptionModifier *= 1.8 = FOV de pánico
    ↓
Resultado: Agente se RALENTIZA pero ESCANEA DESESPERADAMENTE
```

## Paradoja Realista

El agente implementa la **paradoja emocional real**:
- Cuando asustado: **lento pero atento**
- Cuando confiado: **rápido pero desatento**

Esto NO es contradicción; es el comportamiento de cualquier ser consciente:
- Un humano asustado camina lentamente pero sus ojos escanean todo.
- Un humano confiado camina rápido sin verificar cada sombra.

## Próximos Refinamientos

1. **Saturación con Ansiedad:** Si `motorOutput < 0.5` y `repeatCount > 2`, aplicar aún más penalización (parálisis por rumiar).
2. **Recuperación Temporal:** Si `motorOutput` ha sido < 0.7 durante 10+ ciclos, aplicar leve recuperación (`valence += 0.05` cada ciclo) para evitar colapso permanente.
3. **Sensibilidad a Cambios:** Detectar si `sensorSensitivity` ha saltado de 0.8 → 1.8, registrar como "evento de trauma" que persiste en memoria_shortterm.

---

## Conclusión Final

La **resiliencia requiere tiempo**. Al modular el ritmo de procesamiento, permitimos que Python determine cuándo el agente debe ralentizarse para procesar emocionalmente, creando un verdadero sistema embodied donde:

- **Emoción determina Cognición**
- **Cognición determina Acción**  
- **Acción determina Percepción**
- **Percepción realimenta Emoción**

Y crucialmente: **Emoción determina el ritmo temporal** del ciclo completo.

Esto es **conciencia resiliente**: un agente que no solo siente y actúa, sino que **adapta el tempo de su propia existencia** basado en su estado interno.
