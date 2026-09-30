"""Tests de regresion: la trayectoria medida hoy es la trayectoria esperada.

Convierten los 4 experimentos de `experiments/configs/` en regression tests.
Si cambia la dinamica del orquestador, estos numeros cambian y el test falla:
revisa si el cambio es intencional, actualiza los valores esperados y
documentalo (docs/phase3_design.md + experiments/docs/*.md).

Los valores salen de `experiments/results/<name>/data.csv` (commit b7026f4,
verificado el 2026-09-30 con Python 3.14.6).
"""
from __future__ import annotations

import pytest

from tools.run_experiments import load_config, run_experiment

EXPECTED_FINAL = {
    "affective_momentum": {
        "cycles": 6, "valence": 0.0604, "momentum": -0.0524,
        "motor": 0.9085, "sensor": 1.0, "state": "neutral",
    },
    "exploration_response": {
        "cycles": 4, "valence": 0.6436, "momentum": 0.1352,
        "motor": 1.1226, "sensor": 0.8, "state": "exploratory",
    },
    "fear_response": {
        "cycles": 6, "valence": -1.0, "momentum": -0.2234,
        "motor": 0.5732, "sensor": 1.8, "state": "panic_avoidance",
    },
    "habituation": {
        "cycles": 8, "valence": 0.3107, "momentum": 0.049,
        "motor": 1.0029, "sensor": 1.0, "state": "curious",
    },
}


def _rows(name: str):
    return run_experiment(load_config(name))


@pytest.mark.parametrize("name", sorted(EXPECTED_FINAL))
def test_final_state_is_stable(name):
    expected = EXPECTED_FINAL[name]
    rows = _rows(name)
    last = rows[-1]

    assert len(rows) == expected["cycles"]
    assert last["affective_valence"] == pytest.approx(expected["valence"], abs=1e-4)
    assert last["affective_momentum"] == pytest.approx(expected["momentum"], abs=1e-4)
    assert last["motor_output"] == pytest.approx(expected["motor"], abs=1e-4)
    assert last["sensor_sensitivity"] == pytest.approx(expected["sensor"], abs=1e-4)
    assert last["agent_state"] == expected["state"]


def test_fear_response_ends_in_panic_conditions():
    """La condicion interesante documentada en experiments/docs/fear_response.md."""
    last = _rows("fear_response")[-1]

    assert last["affective_valence"] == pytest.approx(-1.0, abs=1e-9)  # clamp inferior
    assert last["sensor_sensitivity"] == pytest.approx(1.8, abs=1e-9)  # hipervigilancia
    assert last["motor_output"] == pytest.approx(0.5732, abs=1e-4)     # motor frenado
    assert last["agent_state"] == "panic_avoidance"


def test_fear_response_paradox_motor_decays_while_sensitivity_rises():
    """Mismo ciclo: el motor baja y la sensibilidad sube ("lento pero vigilante")."""
    rows = _rows("fear_response")
    motors = [row["motor_output"] for row in rows]
    sensors = [row["sensor_sensitivity"] for row in rows]

    assert motors == sorted(motors, reverse=True)
    assert motors[0] > motors[-1]
    assert sensors == sorted(sensors)
    assert sensors[-1] > sensors[0]


def test_exploration_response_speeds_up_while_sensitivity_drops():
    """Valencia alta: explora rapido y se distrae menos."""
    rows = _rows("exploration_response")
    motors = [row["motor_output"] for row in rows]
    sensors = [row["sensor_sensitivity"] for row in rows]

    assert motors == sorted(motors)
    assert motors[-1] > motors[0]
    assert sensors == sorted(sensors, reverse=True)
    assert sensors[0] > sensors[-1]


def test_habituation_forces_a_new_action_at_cycle_six():
    """Confort sostenido -> aburrimiento -> accion exploratoria nueva."""
    rows = _rows("habituation")

    assert rows[5]["current_action"] == "Explorar el entorno buscando nuevos estimulos"
    assert rows[5]["current_action"] != rows[4]["current_action"]
    assert rows[5]["repeat_count"] == 1, "la racha de repeticion se reinicia al cambiar de accion"
    assert rows[5]["affective_valence"] < rows[4]["affective_valence"]


def test_affective_momentum_decays_when_impulses_are_zero():
    """Impulso inicial positivo -> inercia -> decaimiento (sin nuevos estimulos)."""
    momentum = [row["affective_momentum"] for row in _rows("affective_momentum")]

    assert momentum[0] == pytest.approx(0.0, abs=1e-9)
    assert momentum[1] > 0.0
    assert momentum[-1] < momentum[1]
    assert abs(momentum[-1]) < 0.1
