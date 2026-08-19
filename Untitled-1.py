# -*- coding: utf-8 -*-
import argparse
import json
import socket
import time

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

class CognitiveOrchestrator:
    """Gestiona el ciclo perceptivo, cognitivo y de decisión."""

    def __init__(self, model_path=None):
        self.llm = None
        self.affective_alpha = 0.6
        self.affective_history_window = 4
        self.affective_decayRate = 0.95  # Decay factor per cycle (0.95 = 5% decay per cycle)
        self.cycles_in_comfort = 0
        self.state = {
            "location": "Sala Principal del Laboratorio Hart.",
            "affective_valence": -0.2,
            "affective_momentum": 0.0,
            "memory_shortterm": [],
            "light_level": "Desconocido",
            "proximity_to_object_meters": 999.0,
            "current_action": "INACTIVO",
        }

        if model_path and Llama is not None:
            print("Iniciando conexion con GGUF Model...")
            try:
                self.llm = Llama(model_path=model_path, n_ctx=4096, verbose=False)
            except Exception as exc:
                print(f"[ERROR LLM] Fallo al cargar GGUF Model. Se usara heuristica local: {exc}")
        elif model_path and Llama is None:
            print("[ERROR LLM] llama_cpp no esta disponible. Se usara heuristica local.")


    def perceive_and_update(self, sensory_data):
        """Recibe datos del mundo (Java/Unreal) y actualiza el estado."""
        print("\n--- PERCEPCIÓN ---")
        self.state["light_level"] = sensory_data.get("lightLevel", "Desconocido")
        self.state["proximity_to_object_meters"] = sensory_data.get(
            "proximityToObjectMeters", 999.0
        )
        self.state["current_action"] = sensory_data.get("currentAction", "INACTIVO")
        self.state["memory_shortterm"].append(
            {
                "sequence": sensory_data.get("sequence"),
                "lightLevel": self.state["light_level"],
                "distance": self.state["proximity_to_object_meters"],
            }
        )
        self.state["memory_shortterm"] = self.state["memory_shortterm"][-6:]

        print(
            f"Luz={self.state['light_level']} | Distancia={self.state['proximity_to_object_meters']:.3f} | "
            f"Accion actual={self.state['current_action']}"
        )

    def compute_agent_state(self):
        """Determine agent behavioral state based on affective_valence and momentum."""
        valence = self.state["affective_valence"]
        momentum = self.state["affective_momentum"]
        
        if valence > 0.6:
            return "exploratory"  # Alta curiosidad, agresivamente exploratorio
        elif valence > 0.2:
            return "curious"  # Curiosidad moderada
        elif valence > -0.2:
            return "neutral"  # Estado equilibrado
        elif valence > -0.5:
            return "cautious"  # Defensivo, cauteloso
        elif valence > -0.8:
            return "seeking_safety"  # Buscando refugio
        else:
            return "panic_avoidance"  # Pánico, máxima defensa

    def compute_motor_output(self):
        """
        Calcula el factor de velocidad motor basado en valencia y momentum.
        Rango: 0.3 (muy lento, casi paralizado) a 1.5 (hiperkinético).
        
        Resiliencia: cuando el agente está asustado, se mueve lentamente (conserva energía).
        Cuando está confiado, se mueve rápido (explora activamente).
        """
        valence = self.state["affective_valence"]
        momentum = self.state["affective_momentum"]
        
        # Base: valencia determina la velocidad base
        # valence -1.0 → 0.3 (prácticamente paralizado)
        # valence +1.0 → 1.5 (hiperkinético)
        base_motor = 0.9 + (valence * 0.3)  # rango [0.6, 1.2]
        
        # Modificar con momentum (inercia afectiva)
        # Si momentum es negativo, ralentiza más (rumiar, parálisis)
        # Si momentum es positivo, acelera (flow state)
        momentum_modifier = 1.0 + (momentum * 0.2)  # rango [0.8, 1.2]
        
        motor_output = base_motor * momentum_modifier
        
        # Clamp entre 0.3 y 1.5
        return max(0.3, min(1.5, motor_output))

    def compute_sensor_sensitivity(self):
        """
        Calcula la sensibilidad sensorial (amplitud del FOV y thresholds).
        Rango: 0.5 (túnel extremo) a 1.8 (hipervigilancia total).
        
        Resiliencia paradójica: cuando el agente está asustado, la sensibilidad SUBE
        porque está en "modo alerta". Cuando está relajado, baja.
        """
        valence = self.state["affective_valence"]
        momentum = self.state["affective_momentum"]
        
        # Patrón invertido respecto a motor_output:
        # Valencia BAJA → sensibilidad ALTA (hipervigilancia por miedo)
        # Valencia ALTA → sensibilidad MEDIA-BAJA (confianza, exploración serena)
        if valence > 0.5:
            # Exploratorio: confiado, reduce sensibilidad (menos ruido)
            base_sensitivity = 0.8
        elif valence > -0.3:
            # Neutral: sensibilidad normal
            base_sensitivity = 1.0
        elif valence > -0.7:
            # Cauteloso: sensibilidad aumentada (vigilancia)
            base_sensitivity = 1.3
        else:
            # Pánico: hipervigilancia extrema
            base_sensitivity = 1.8
        
        # Si hay momentum negativo (estado afectivo deteriorándose), suma urgencia
        if momentum < -0.2:
            base_sensitivity *= 1.2  # Amplifica más la alerta
        
        return max(0.5, min(1.8, base_sensitivity))

    def heuristic_response(self):
        light_level = self.state["light_level"]
        distance = self.state["proximity_to_object_meters"]
        valence = self.state["affective_valence"]

        if light_level == "Alto" and distance < 1.0:
            thought = "La cercania y la alta iluminacion disparan curiosidad exploratoria."
            action = "Examinar objeto rojo con curiosidad intensa"
        elif light_level == "Bajo" and distance > 3.0:
            thought = "La oscuridad y la distancia aumentan cautela y busqueda de orientacion."
            action = "Caminar lentamente buscando una fuente de iluminacion"
        elif light_level == "Medio" and valence > 0.35:
            thought = "El entorno parece seguro y la valencia positiva sostiene una exploracion serena."
            action = "Explorar el entorno con paso confiado"
        elif light_level == "Medio":
            thought = "El entorno se siente estable; conviene observar antes de actuar."
            action = "Observar entorno con calma y reflexion"
        elif valence < -0.45:
            thought = "La valencia acumulada sigue baja; conviene reducir exposicion y conservar estabilidad."
            action = "Mantener posicion actual"
        else:
            thought = "No hay una señal dominante; mantener postura y esperar nuevos datos es coherente."
            action = "Mantener posicion actual"

        return self.apply_boredom_drive(thought, action)

    def apply_boredom_drive(self, thought, action):
        """Evita estancamiento en zona de confort prolongada forzando exploracion."""
        light_level = self.state["light_level"]
        distance = self.state["proximity_to_object_meters"]

        if light_level == "Alto" and distance < 0.5:
            self.cycles_in_comfort += 1
        else:
            self.cycles_in_comfort = 0

        if self.cycles_in_comfort > 5:
            old_valence = self.state["affective_valence"]
            self.state["affective_valence"] = max(-1.0, min(1.0, old_valence - 0.15))
            self.cycles_in_comfort = 0
            boredom_thought = (
                "El confort sostenido se vuelve estancamiento; necesito nuevos estimulos "
                "para mantener agencia."
            )
            boredom_action = "Explorar el entorno buscando nuevos estimulos"
            print(
                f"[COGNICION] Habituacion detectada: valencia {old_valence:+.2f} -> "
                f"{self.state['affective_valence']:+.2f}."
            )
            return boredom_thought, boredom_action

        return thought, action

    def recent_affective_history(self):
        history = []
        for item in reversed(self.state["memory_shortterm"]):
            if "effectiveAffectiveChange" not in item:
                continue

            history.append(float(item["effectiveAffectiveChange"]))
            if len(history) == self.affective_history_window:
                break

        history.reverse()
        return history

    def compute_historical_inertia(self):
        recent_history = self.recent_affective_history()
        if not recent_history:
            return 0.0

        weighted_total = 0.0
        weight_sum = 0.0
        for index, delta in enumerate(recent_history, start=1):
            weight = index
            weighted_total += delta * weight
            weight_sum += weight

        return weighted_total / weight_sum

    def blend_affective_delta(self, direct_delta):
        historical_inertia = self.compute_historical_inertia()
        effective_delta = (
            self.affective_alpha * direct_delta
            + (1.0 - self.affective_alpha) * historical_inertia
        )
        return effective_delta, historical_inertia

    def apply_feedback(self, feedback_payload):
        direct_delta = float(feedback_payload.get("affectiveChange", 0.0))
        rationale = feedback_payload.get("rationale", "Sin racional explicita.")
        action_taken = feedback_payload.get("actionTaken", self.state["current_action"])
        effective_delta, historical_inertia = self.blend_affective_delta(direct_delta)

        # Decaimiento temporal: la valencia se acerca a 0 antes de sumar el nuevo impulso
        old_valence = self.state["affective_valence"]
        decayed_valence = old_valence * self.affective_decayRate

        # Sumar el nuevo impulso (ya incluye inercia)
        new_valence = max(-1.0, min(1.0, decayed_valence + effective_delta))
        self.state["affective_valence"] = new_valence
        self.state["affective_momentum"] = historical_inertia
        self.state["current_action"] = action_taken
        self.state["memory_shortterm"].append(
            {
                "sequence": feedback_payload.get("sequence"),
                "actionTaken": action_taken,
                "directAffectiveChange": direct_delta,
                "historicalInertia": historical_inertia,
                "effectiveAffectiveChange": effective_delta,
                "valenceBeforeDecay": old_valence,
                "valenceAfterDecay": decayed_valence,
                "rationale": rationale,
            }
        )
        self.state["memory_shortterm"] = self.state["memory_shortterm"][-6:]

        print("\n--- FEEDBACK AFECTIVO ---")
        print(
            f"Accion ejecutada={action_taken} | DeltaAccion={direct_delta:+.2f} | "
            f"Inercia={historical_inertia:+.2f} | DeltaTotal={effective_delta:+.2f} | "
            f"Valencia antes/decay={old_valence:+.2f}/{decayed_valence:+.2f} | "
            f"Valencia actual={self.state['affective_valence']:+.2f}"
        )
        print(f"Rationale={rationale}")

    def generate_internal_monologue(self):
        """Consulta al GGUF para generar el pensamiento basado en la heurística afectiva."""
        if self.llm is None:
            return self.heuristic_response()

        prompt = (
            "Eres un ser consciente simulado. "
            f"Tu estado actual emocional ('affective_valence') es {self.state['affective_valence']:.2f}. "
            f"Tu inercia afectiva reciente ('affective_momentum') es {self.state['affective_momentum']:.2f}. "
            f"memory_shortterm contiene: {json.dumps(self.state['memory_shortterm'], ensure_ascii=False)}. "
            f"La ubicacion actual es '{self.state['location']}'. "
            f"El nivel de luz es '{self.state['light_level']}' y la proximidad es {self.state['proximity_to_object_meters']:.3f}. "
            "Responde solo con JSON: {'thought': '...', 'desired_action': '...'}"
        )

        try:
            output = self.llm.create_completion(prompt, max_tokens=256, temperature=0.7)
            raw_text = output["choices"][0]["text"].strip()
            json_start = raw_text.find("{")
            json_end = raw_text.rfind("}")
            payload = json.loads(raw_text[json_start : json_end + 1])
            return self.apply_boredom_drive(payload["thought"], payload["desired_action"])
        except Exception as exc:
            print(f"[ERROR LLM] No se pudo decodificar la respuesta JSON del GGUF: {exc}")
            return self.heuristic_response()


def run_socket_client(host, port, orchestrator):
    print(f"Conectando a Java en {host}:{port}...")
    with socket.create_connection((host, port), timeout=10.0) as sock:
        sock.settimeout(None)
        reader = sock.makefile("r", encoding="utf-8")
        writer = sock.makefile("w", encoding="utf-8")

        for raw_line in reader:
            payload = json.loads(raw_line)
            message_type = payload.get("type")

            if message_type == "perception":
                orchestrator.perceive_and_update(payload)
                thought, desired_action = orchestrator.generate_internal_monologue()

                print("\n--- COGNICIÓN ---")
                print(f"Monólogo Interno: {thought}")
                print(f"Acción Elegida: {desired_action}")

                agent_state = orchestrator.compute_agent_state()
                motor_output = orchestrator.compute_motor_output()
                sensor_sensitivity = orchestrator.compute_sensor_sensitivity()
                response = {
                    "type": "command",
                    "sequence": payload.get("sequence"),
                    "command": desired_action,
                    "thought": thought,
                    "affectiveValence": orchestrator.state["affective_valence"],
                    "affectiveMomentum": orchestrator.state["affective_momentum"],
                    "agentState": agent_state,
                    "motorOutput": motor_output,
                    "sensorSensitivity": sensor_sensitivity,
                }
                writer.write(json.dumps(response, ensure_ascii=False) + "\n")
                writer.flush()
            elif message_type == "feedback":
                orchestrator.apply_feedback(payload)


def run_forever(host, port, orchestrator, reconnect_delay):
    while True:
        try:
            run_socket_client(host, port, orchestrator)
            print("[BRIDGE] Java cerro la conexion. Reintentando enlace...")
        except (ConnectionError, OSError, json.JSONDecodeError) as exc:
            print(f"[BRIDGE] Conexion interrumpida o invalida. Reintentando: {exc}")

        time.sleep(reconnect_delay)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cliente cognitivo Python para CharacterBody.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--reconnect-delay", type=float, default=2.0)
    args = parser.parse_args()

    orchestrator = CognitiveOrchestrator(model_path=args.model_path)

    print("================ PUENTE PYTHON↔JAVA INICIADO ================")
    try:
        run_forever(args.host, args.port, orchestrator, args.reconnect_delay)
    except KeyboardInterrupt:
        print("\n[SYSTEM SHUTDOWN] Ciclo de Conciencia detenido por el usuario.")
    except Exception as exc:
        print(f"[ERROR BRIDGE] Fallo la comunicacion con Java: {exc}")
