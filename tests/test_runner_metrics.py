"""Tests de las metricas observacionales del runner.

`observational_metrics` no reimplementa `computeSaturationFactor` de Java: solo
OBSERVA la secuencia de acciones (repeticiones consecutivas y switch-rate).
Estos tests fijan esa semantica, que es la que llena las columnas `repeat_count`
y `switch_rate` del CSV.
"""
from __future__ import annotations

import pytest

from tools.run_experiments import load_config, observational_metrics, run_experiment


@pytest.mark.parametrize(
    "actions,expected_repeat,expected_switch",
    [
        (["A"], 1, 0.0),
        (["A", "A", "A"], 3, 0.0),
        (["A", "B"], 1, 1.0),
        (["A", "A", "B", "B"], 2, 1.0 / 3.0),
        (["A", "B", "A"], 1, 1.0),
        (["A", "B", "C", "D"], 1, 1.0),
    ],
)
def test_observational_metrics_semantics(actions, expected_repeat, expected_switch):
    repeat, switch = observational_metrics(actions)
    assert repeat == expected_repeat
    assert switch == pytest.approx(expected_switch, abs=1e-9)


def test_switch_rate_is_bounded():
    rows = run_experiment(load_config("habituation"))
    for row in rows:
        assert 0.0 <= row["switch_rate"] <= 1.0
        assert 1 <= row["repeat_count"] <= len(rows)


def test_repeat_count_matches_the_observed_action_history():
    """Contraste independiente: recalcular desde las acciones del CSV."""
    rows = run_experiment(load_config("fear_response"))
    actions = [row["current_action"] for row in rows]
    for index, row in enumerate(rows):
        observed_repeat, observed_switch = observational_metrics(actions[: index + 1])
        assert row["repeat_count"] == observed_repeat
        assert row["switch_rate"] == pytest.approx(observed_switch, abs=1e-4)
