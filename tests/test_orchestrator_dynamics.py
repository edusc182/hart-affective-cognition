"""Tests unitarios de la dinamica programada del orquestador.

Aislan los umbrales documentados (maquina de estados, motor, sensibilidad,
habituacion) para que un cambio silencioso de comportamiento falle aqui y no
solo en los tests de trayectoria.
"""
from __future__ import annotations

import pytest

from orchestrator.orchestrator import CognitiveOrchestrator


def _orchestrator(valence: float = 0.0, momentum: float = 0.0) -> CognitiveOrchestrator:
    orch = CognitiveOrchestrator(model_path=None)  # LLM desactivado: heuristica pura
    orch.state["affective_valence"] = valence
    orch.state["affective_momentum"] = momentum
    return orch


@pytest.mark.parametrize(
    "valence,expected_state",
    [
        (0.9, "exploratory"),
        (0.4, "curious"),
        (0.0, "neutral"),
        (-0.35, "cautious"),
        (-0.6, "seeking_safety"),
        (-0.9, "panic_avoidance"),
    ],
)
def test_agent_state_thresholds(valence, expected_state):
    assert _orchestrator(valence).compute_agent_state() == expected_state


@pytest.mark.parametrize("valence", [-1.0, -0.5, 0.0, 0.5, 1.0])
def test_modulators_stay_inside_declared_ranges(valence):
    orch = _orchestrator(valence)
    assert 0.3 <= orch.compute_motor_output() <= 1.5
    assert 0.5 <= orch.compute_sensor_sensitivity() <= 1.8


@pytest.mark.parametrize("momentum", [-1.0, -0.5, 0.0, 0.5, 1.0])
def test_momentum_does_not_break_the_ranges(momentum):
    orch = _orchestrator(0.0, momentum)
    assert 0.3 <= orch.compute_motor_output() <= 1.5
    assert 0.5 <= orch.compute_sensor_sensitivity() <= 1.8


def test_emotional_paradox_at_the_extremes():
    """Asustado: lento pero hipervigilante. Confiado: rapido y poco sensible."""
    afraid = _orchestrator(-1.0)
    calm = _orchestrator(1.0)

    assert afraid.compute_motor_output() < calm.compute_motor_output()
    assert afraid.compute_sensor_sensitivity() > calm.compute_sensor_sensitivity()


def test_negative_momentum_amplifies_vigilance():
    baseline = _orchestrator(-0.5, 0.0).compute_sensor_sensitivity()
    deteriorating = _orchestrator(-0.5, -0.5).compute_sensor_sensitivity()
    assert deteriorating >= baseline


def test_valence_is_clamped_when_feedback_pushes_out_of_range():
    orch = _orchestrator(0.9)
    orch.apply_feedback({"actionTaken": "a", "affectiveChange": 0.9, "rationale": "r"})
    assert orch.state["affective_valence"] == pytest.approx(1.0, abs=1e-9)

    orch = _orchestrator(-0.9)
    orch.apply_feedback({"actionTaken": "a", "affectiveChange": -0.9, "rationale": "r"})
    assert orch.state["affective_valence"] == pytest.approx(-1.0, abs=1e-9)


def test_boredom_drive_needs_six_comfort_cycles():
    """`apply_boredom_drive`: solo rompe la fijacion a partir del 6.o ciclo comodo."""
    orch = _orchestrator(0.5)
    orch.state["light_level"] = "Alto"
    orch.state["proximity_to_object_meters"] = 0.4

    for _ in range(5):
        thought, action = orch.apply_boredom_drive("pensamiento", "accion")
        assert (thought, action) == ("pensamiento", "accion")

    assert orch.cycles_in_comfort == 5
    thought, action = orch.apply_boredom_drive("pensamiento", "accion")
    assert "nuevos estimulos" in action
    assert orch.state["affective_valence"] == pytest.approx(0.5 - 0.15, abs=1e-9)
    assert orch.cycles_in_comfort == 0


def test_comfort_counter_resets_outside_the_comfort_zone():
    orch = _orchestrator(0.5)
    orch.state["light_level"] = "Alto"
    orch.state["proximity_to_object_meters"] = 0.4
    orch.apply_boredom_drive("t", "a")
    assert orch.cycles_in_comfort == 1

    orch.state["proximity_to_object_meters"] = 2.0
    orch.apply_boredom_drive("t", "a")
    assert orch.cycles_in_comfort == 0
