"""Contrato del protocolo Java <-> Python (preparacion de la Fase 3c).

Estos tests NO ejecutan Java todavia. Verifican que:

1. los mensajes/tipos y las claves del protocolo estan declarados en las fuentes
   Java y consumidos por el orquestador Python (contrato alineado), y
2. el orquestador tolera el JSON real de Java, incluida la telemetria de
   saturacion de la Fase 3d.

El hueco real de la Fase 3c queda fijado explicitamente en el ultimo test: el
protocolo TRANSPORTA `saturationFactor`, pero la trayectoria validada es
in-process, asi que la columna sale vacia. Cuando aterrice la integracion TCP
habra que sustituir ese test por uno end-to-end real (Java + Python en vivo).
"""
from __future__ import annotations

import pytest

from orchestrator.orchestrator import CognitiveOrchestrator
from tools.run_experiments import COLUMNS, ROOT, load_config, run_experiment

BRIDGE_SRC = ROOT / "java_body" / "CognitiveSocketBridge.java"
FEEDBACK_SRC = ROOT / "java_body" / "FeedbackData.java"
CHARACTER_SRC = ROOT / "java_body" / "CharacterBody.java"
ORCHESTRATOR_SRC = ROOT / "orchestrator" / "orchestrator.py"

MESSAGE_TYPES = ("perception", "command", "feedback")

PERCEPTION_KEYS = ("type", "sequence", "lightLevel", "proximityToObjectMeters", "currentAction")
COMMAND_KEYS = ("affectiveValence", "affectiveMomentum", "agentState", "motorOutput", "sensorSensitivity")
FEEDBACK_KEYS = ("actionTaken", "affectiveChange", "rationale",
                 "saturationFactor", "repeatCount", "switchRate")


def test_message_type_tags_match_on_both_sides():
    java = BRIDGE_SRC.read_text(encoding="utf-8")
    python = ORCHESTRATOR_SRC.read_text(encoding="utf-8")

    for tag in MESSAGE_TYPES:
        assert f'"{tag}"' in java, f"Java no declara el tipo de mensaje {tag!r}"
        assert f'"{tag}"' in python, f"Python no maneja el tipo de mensaje {tag!r}"


@pytest.mark.parametrize("key", PERCEPTION_KEYS + COMMAND_KEYS + FEEDBACK_KEYS)
def test_protocol_keys_are_declared_in_the_java_side(key):
    assert key in BRIDGE_SRC.read_text(encoding="utf-8")


@pytest.mark.parametrize("key", PERCEPTION_KEYS + COMMAND_KEYS)
def test_protocol_keys_are_consumed_by_the_python_side(key):
    assert key in ORCHESTRATOR_SRC.read_text(encoding="utf-8")


def test_saturation_telemetry_is_part_of_the_java_feedback_contract():
    """Fase 3d: `FeedbackData` expone la telemetria y `CharacterBody` la emite opt-in."""
    feedback = FEEDBACK_SRC.read_text(encoding="utf-8")
    for key in ("saturationFactor", "repeatCount", "switchRate"):
        assert key in feedback

    character = CHARACTER_SRC.read_text(encoding="utf-8")
    assert "HART_TELEMETRY" in character, "la telemetria debe seguir siendo opt-in y flaggeada"
    assert "HART_TELEMETRY" in (ROOT / "README.md").read_text(encoding="utf-8")


def test_python_consumer_tolerates_the_real_java_feedback_payload():
    """El JSON de Java (con campos nuevos) no debe romper al orquestador."""
    orch = CognitiveOrchestrator(model_path=None)
    orch.perceive_and_update({
        "lightLevel": "Bajo",
        "proximityToObjectMeters": 3.2,
        "currentAction": "INACTIVO",
        "sequence": 1,
    })

    java_style_feedback = {
        "type": "feedback",
        "sequence": 1,
        "lightLevel": "Bajo",
        "proximityToObjectMeters": 3.2,
        "actionTaken": "Caminar lentamente buscando una fuente de iluminacion",
        "affectiveChange": -0.12,
        "rationale": "La navegacion cautelosa en baja luz incrementa tension y vigilancia.",
        "saturationFactor": 0.85,
        "repeatCount": 3,
        "switchRate": 0.25,
    }

    orch.apply_feedback(java_style_feedback)

    assert -1.0 <= orch.state["affective_valence"] <= 1.0
    assert orch.state["current_action"] == "Caminar lentamente buscando una fuente de iluminacion"
    assert orch.state["memory_shortterm"][-1]["sequence"] == 1


def test_saturation_columns_exist_in_the_csv_schema():
    """Cuando la Fase 3c aterrice, las columnas ya estan declaradas en el CSV."""
    assert "saturation_factor" in COLUMNS
    assert "repeat_count" in COLUMNS
    assert "switch_rate" in COLUMNS


def test_saturation_column_is_still_empty_in_the_in_process_trajectory():
    """Fija el UNICO hueco funcional de la Fase 3c.

    El protocolo ya transporta `saturationFactor` (Java, Fase 3d), pero la
    trayectoria experimental validada es in-process (`run_experiment` importa el
    orquestador, no habla con Java), asi que la columna se emite vacia.
    No hay todavia ninguna prueba automatizada que demuestre el protocolo en
    ejecucion real: ese es el objetivo de la Fase 3c.
    """
    rows = run_experiment(load_config("fear_response"))
    assert all(row["saturation_factor"] == "" for row in rows)
