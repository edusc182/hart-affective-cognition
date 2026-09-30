"""Integracion REAL Java <-> Python (Fase 3c).

Java se trata como un **proceso externo**: aqui nunca se importa ni se simula
`CharacterBody`; el test habla el protocolo TCP/JSON real contra el cuerpo Java.

Criterios (inequívocos, tal como se definieron para cerrar la Fase 3):

    display disponible  -> RUN
    display ausente     -> SKIP explicito (nunca pass silencioso)
    Java no arranca     -> FAIL
    protocolo/TCP falla -> FAIL
    telemetria ausente  -> FAIL

Requiere `java_body/classes` compilado. Esta suite es la unica del proyecto que
necesita Java: `tests/unit/` sigue siendo la validacion in-process determinista.
"""
from __future__ import annotations

import csv
import socket
import time

import pytest

from tools.run_integration import (
    COLUMNS,
    IntegrationError,
    environment_problems,
    is_launcher_path,
    java_candidates,
    java_executable,
    run_integration,
    telemetry_mismatches,
    validate_rows,
    write_csv,
)

pytestmark = pytest.mark.integration

CYCLES = 8


@pytest.fixture(scope="module")
def session_result():
    problems = environment_problems()
    if problems:
        pytest.skip("integracion no ejecutable en este entorno: " + "; ".join(problems))
    return run_integration(cycles=CYCLES, quiet=True)


def test_java_runs_as_an_external_process(session_result):
    assert session_result["status"] == "ok"
    assert "CharacterBody" in " ".join(session_result["java_cmd"])
    assert session_result["java_exit_code"] is not None, (
        "el proceso Java debe terminar de forma limpia, no quedar colgado")


def test_protocol_completes_the_configured_cycles(session_result):
    rows = session_result["rows"]
    assert len(rows) == CYCLES
    assert [row["cycle"] for row in rows] == list(range(1, CYCLES + 1))
    assert all(row["action_taken"] for row in rows)


def test_saturation_telemetry_from_java_lands_in_the_python_trajectory(session_result):
    """El objetivo de la Fase 3c: la telemetria de Java aparece realmente en Python."""
    rows = session_result["rows"]
    validate_rows(rows)  # falla si saturationFactor/repeatCount/switchRate faltan o son invalidos
    assert all(isinstance(row["python_valence_after"], float) for row in rows)
    assert all(row["python_agent_state"] for row in rows)


def test_protocol_and_stdout_telemetry_agree(session_result):
    """Dos canales independientes (JSON del protocolo y linea HART_TELEMETRY) deben coincidir."""
    assert session_result["telemetry_rows"], (
        "se esperaban lineas HART_TELEMETRY de stdout: Java se lanzo con -DHART_TELEMETRY=true")
    mismatches = telemetry_mismatches(session_result["rows"])
    assert mismatches == [], f"protocolo y stdout no coinciden: {mismatches}"


def test_csv_records_the_java_telemetry(session_result, tmp_path):
    path = tmp_path / "data.csv"
    write_csv(session_result["rows"], path)

    with open(path, newline="", encoding="utf-8") as fh:
        written = list(csv.DictReader(fh))

    assert list(written[0].keys()) == COLUMNS
    assert all(row["saturation_factor"] != "" for row in written)
    assert all(row["repeat_count"] != "" for row in written)
    assert all(row["switch_rate"] != "" for row in written)


def test_port_is_released_after_shutdown(session_result):
    """No queda JVM (ni ventana) viva: el puerto deja de aceptar conexiones.

    Este test cazo un bug real: en Windows `javapath\\java.exe` es un lanzador, asi
    que matar el stub dejaba la JVM huerfana escuchando en el puerto.
    """
    host, port = session_result["host"], session_result["port"]
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                time.sleep(0.2)
        except OSError:
            return  # puerto cerrado: no queda proceso Java
    pytest.fail(f"el puerto {port} sigue aceptando conexiones tras la sesion")


def test_java_executable_prefers_a_real_jvm_over_a_launcher():
    """Regresion del bug del lanzador: si hay un JDK real, no se elige el stub."""
    candidates = java_candidates()
    chosen = java_executable()

    assert chosen is not None, "se esperaba al menos un java disponible"
    assert chosen in candidates

    launchers = [item for item in candidates if is_launcher_path(item)]
    real = [item for item in candidates if not is_launcher_path(item)]
    if not launchers or not real:
        pytest.skip("este entorno no distingue lanzador de JVM real")
    assert not is_launcher_path(chosen), f"se eligio un lanzador: {chosen}"


def test_validator_fails_when_telemetry_is_missing():
    """Telemetria ausente -> FAIL explicito (nunca skip silencioso)."""
    with pytest.raises(IntegrationError):
        validate_rows([])
    with pytest.raises(IntegrationError):
        validate_rows([{"cycle": 1, "saturation_factor": ""}])
    with pytest.raises(IntegrationError):
        validate_rows([{"cycle": 1, "saturation_factor": 1.0, "repeat_count": 0, "switch_rate": 0.0}])
