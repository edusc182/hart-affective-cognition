"""Invariantes y determinismo de la dinamica afectiva REAL.

Regla de oro: se mide el sistema real. `run_experiment` importa el
`CognitiveOrchestrator` de verdad (`orchestrator/orchestrator.py`) con el LLM
desactivado; aqui no se reimplementa ninguna formula de motor, sensibilidad,
valencia ni momentum.
"""
from __future__ import annotations

import pytest

from tools.run_experiments import COLUMNS, CONFIG_DIR, load_config, run_experiment

CONFIG_NAMES = sorted(path.stem for path in CONFIG_DIR.glob("*.json"))

AGENT_STATES = {
    "exploratory",
    "curious",
    "neutral",
    "cautious",
    "seeking_safety",
    "panic_avoidance",
}

# Rangos declarados en orchestrator/orchestrator.py
# (compute_motor_output / compute_sensor_sensitivity / apply_feedback).
VALENCE_MIN, VALENCE_MAX = -1.0, 1.0
MOTOR_MIN, MOTOR_MAX = 0.3, 1.5
SENSOR_MIN, SENSOR_MAX = 0.5, 1.8


def _without_timestamps(rows):
    """`timestamp` mide tiempo real de pared: no puede compararse entre runs."""
    return [{k: v for k, v in row.items() if k != "timestamp"} for row in rows]


def test_configs_are_present():
    assert CONFIG_NAMES, "no hay configs en experiments/configs/*.json"


@pytest.mark.parametrize("name", CONFIG_NAMES)
def test_trajectory_is_deterministic(name):
    """Mismo seed + misma config -> misma trayectoria (evidencia reproducible)."""
    cfg = load_config(name)
    first = _without_timestamps(run_experiment(cfg))
    second = _without_timestamps(run_experiment(cfg))
    assert first == second, f"{name} no es determinista"


@pytest.mark.parametrize("name", CONFIG_NAMES)
def test_cycle_count_and_sequence_follow_the_config(name):
    cfg = load_config(name)
    rows = run_experiment(cfg)
    expected = int(cfg["cycles"])
    assert len(rows) == expected
    assert [row["cycle"] for row in rows] == list(range(1, expected + 1))
    assert [row["sequence"] for row in rows] == list(range(1, expected + 1))


@pytest.mark.parametrize("name", CONFIG_NAMES)
def test_csv_schema_is_stable(name):
    rows = run_experiment(load_config(name))
    for row in rows:
        assert list(row.keys()) == COLUMNS


@pytest.mark.parametrize("name", CONFIG_NAMES)
def test_state_and_modulator_invariants_hold(name):
    rows = run_experiment(load_config(name))
    for row in rows:
        assert VALENCE_MIN <= row["affective_valence"] <= VALENCE_MAX
        assert VALENCE_MIN <= row["affective_momentum"] <= VALENCE_MAX
        assert MOTOR_MIN <= row["motor_output"] <= MOTOR_MAX
        assert SENSOR_MIN <= row["sensor_sensitivity"] <= SENSOR_MAX
        assert row["agent_state"] in AGENT_STATES
        assert row["repeat_count"] >= 1
        assert 0.0 <= row["switch_rate"] <= 1.0
        assert row["thought"], "el monologo interno nunca debe quedar vacio"
        assert row["rationale"], "el rationale del feedback nunca debe quedar vacio"


@pytest.mark.parametrize("name", CONFIG_NAMES)
def test_momentum_column_mirrors_historical_inertia(name):
    """`affective_momentum` es la inercia historica (misma fuente en el orquestador)."""
    rows = run_experiment(load_config(name))
    for row in rows:
        assert row["affective_momentum"] == row["historical_inertia"]


@pytest.mark.parametrize("name", CONFIG_NAMES)
def test_valence_follows_the_sign_of_the_net_stimulus(name):
    """La valencia final refleja el signo del impulso afectivo acumulado."""
    cfg = load_config(name)
    net = sum(cfg["stimulus"]["affective_change"])
    if abs(net) < 1e-9:
        pytest.skip(f"{name}: impulso neto nulo, sin expectativa de signo")

    initial = float(cfg["initial_state"]["affective_valence"])
    final = run_experiment(cfg)[-1]["affective_valence"]
    assert (final > initial) if net > 0 else (final < initial)
