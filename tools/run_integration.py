#!/usr/bin/env python3
r"""run_integration.py - validacion de la integracion REAL Java <-> Python (Fase 3c).

Separacion conceptual con el resto del proyecto (regla de oro):

    tools/run_experiments.py  -> validacion DETERMINISTA del CognitiveOrchestrator
                                 in-process (sin Java, sin GUI, sin GGUF).

    tools/run_integration.py  -> validacion del SISTEMA COMPLETO:
                                 Python <-> TCP/JSON <-> Java CharacterBody <-> telemetria.

Este runner NO reimplementa dinamica afectiva: importa el `CognitiveOrchestrator`
real y usa sus metodos publicos (`perceive_and_update`, `generate_internal_monologue`,
`apply_feedback`, `compute_motor_output`, `compute_sensor_sensitivity`,
`compute_agent_state`). Lo unico propio es la capa de I/O acotada: arranque/parada
del proceso Java, bucle de sockets con timeout y registro en CSV.

Que demuestra: que `saturationFactor`, `repeatCount` y `switchRate` que genera Java
(Fase 3d) atraviesan realmente el protocolo y llegan a la trayectoria Python.

Requisitos: JDK (`java` en el PATH), clases compiladas en `java_body/classes`
(`javac -d classes`) y **display disponible** (el cuerpo crea la ventana Swing).
Sin display la integracion se marca como *skip*: ausencia de display NO es un pass.

Nota Windows (hallazgo real del propio test de integracion): `javapath\java.exe` es un
**lanzador ejecutable**, no un symlink. Terminar ese stub deja la JVM real huerfana
(con su ventana y su puerto vivos), asi que el harness prefiere una JVM real y, ademas,
mata el arbol del proceso y cualquier PID que siga escuchando en el puerto, verificando
al final que el puerto quedo cerrado.

Uso:
    python tools/run_integration.py --cycles 10
    python tools/run_integration.py --cycles 6 --no-telemetry-flag
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA_BODY_DIR = ROOT / "java_body"
CLASSES_DIR = JAVA_BODY_DIR / "classes"
LIB_JAR = ROOT / "lib" / "gson-2.13.1.jar"
RESULTS_DIR = ROOT / "experiments" / "results" / "integration"

# Rango fijo de puertos (mismo criterio que INIT_LIFE.bat con 5050-5100).
PORT_CANDIDATES = range(5150, 5260)

sys.path.insert(0, str(ROOT))

from orchestrator.orchestrator import CognitiveOrchestrator  # noqa: E402 (orquestador REAL)

TELEMETRY_PREFIX = "HART_TELEMETRY "
BRIDGE_READY_MARKER = "[BRIDGE] Servidor TCP iniciado"

# Rutas que en Windows contienen LANZADORES, no la JVM (ver java_executable()).
LAUNCHER_PATH_HINTS = ("javapath", "common files\\oracle", "common files/oracle")

# Rango declarado en CharacterBody.computeSaturationMetrics (Math.max(0.15, ...)).
SATURATION_MIN, SATURATION_MAX = 0.15, 1.0

COLUMNS = [
    "cycle",
    "sequence",
    "action_taken",
    "affective_change_java",
    "saturation_factor",
    "repeat_count",
    "switch_rate",
    "rationale",
    "stdout_saturation_factor",
    "stdout_repeat_count",
    "stdout_switch_rate",
    "python_valence_after",
    "python_motor_output",
    "python_sensor_sensitivity",
    "python_agent_state",
]


class IntegrationError(RuntimeError):
    """Fallo real de integracion: protocolo, timeout o telemetria ausente/invalida."""


class EnvironmentNotReady(RuntimeError):
    """El entorno no puede ejecutar la integracion (sin JDK, sin clases o sin display)."""


def java_candidates() -> list[str]:
    """Todos los `java` disponibles, en orden de preferencia."""
    raw: list[str] = []
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        raw.append(os.path.join(java_home, "bin", "java.exe" if os.name == "nt" else "java"))

    if os.name == "nt" and shutil.which("where"):
        try:
            proc = subprocess.run(["where", "java"], capture_output=True, text=True, timeout=15)
            raw.extend(line.strip() for line in (proc.stdout or "").splitlines() if line.strip())
        except (OSError, subprocess.SubprocessError):
            pass

    found = shutil.which("java")
    if found:
        raw.append(found)

    unique: list[str] = []
    seen = set()
    for item in raw:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def java_executable() -> str | None:
    """JVM real, evitando lanzadores.

    Hallazgo del test de integracion (Windows): `javapath\\java.exe` es un **lanzador
    ejecutable**, no un symlink. Si se termina ese stub, la JVM real (`java.exe`)
    sobrevive como proceso huerfano conservando la ventana y el puerto. Por eso se
    prefiere cualquier `java` que no viva bajo `javapath`.
    """
    candidates = [item for item in java_candidates() if Path(item).exists()]
    if not candidates:
        return None
    for candidate in candidates:
        if not is_launcher_path(candidate):
            return candidate
    return candidates[0]


def is_launcher_path(path: str) -> bool:
    lowered = path.lower()
    return any(hint in lowered for hint in LAUNCHER_PATH_HINTS)


def has_display() -> bool:
    """Heuristica honesta: sin display el cuerpo no puede crear la ventana Swing."""
    if platform.system() in ("Windows", "Darwin"):
        return True
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        return True
    try:
        import tkinter
        root = tkinter.Tk()
        root.destroy()
        return True
    except Exception:
        return False


def environment_problems() -> list[str]:
    """Precondiciones del entorno (todas se reportan, no solo la primera)."""
    problems = []
    if java_executable() is None:
        problems.append("no se encontro 'java' en el PATH (se requiere JDK/JRE 8+)")
    if not (CLASSES_DIR / "CharacterBody.class").exists():
        problems.append(
            f"faltan las clases compiladas en {CLASSES_DIR} "
            "(javac -cp lib/gson-2.13.1.jar -d java_body/classes java_body/*.java)"
        )
    if not LIB_JAR.exists():
        problems.append(f"falta {LIB_JAR}")
    if not has_display():
        problems.append("no hay display disponible (el cuerpo crea la ventana Swing)")
    return problems


def classpath() -> str:
    return os.pathsep.join([str(CLASSES_DIR), str(LIB_JAR)])


def find_free_port(host: str = "127.0.0.1", candidates=PORT_CANDIDATES) -> int:
    """Puerto libre de un rango fijo (como INIT_LIFE.bat), no del pool efimero.

    Se evita `bind(port=0)` porque el pool efimero de Windows es menos predecible
    para verificar despues que el puerto quedo realmente cerrado.
    """
    for port in candidates:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("", port))
            except OSError:
                continue
            return int(port)
    raise EnvironmentNotReady(
        f"no hay puerto libre en el rango {candidates.start}-{candidates.stop - 1}")


def port_accepts_connections(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def wait_until_port_closed(host: str, port: int, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not port_accepts_connections(host, port):
            return True
        time.sleep(0.1)
    return False


def windows_pids_listening_on(port: int) -> list[int]:
    """PIDs que escuchan en `port` (para matar JVMs huerfanas de lanzadores)."""
    if os.name != "nt":
        return []
    try:
        proc = subprocess.run(["netstat", "-ano", "-p", "TCP"],
                              capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return []

    pids = set()
    for line in (proc.stdout or "").splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[0].upper() == "TCP" and parts[3].upper() == "LISTENING":
            if parts[1].endswith(f":{port}"):
                try:
                    pids.add(int(parts[4]))
                except ValueError:
                    continue
    return sorted(pids)


class JavaBodyProcess:
    """Arranca `CharacterBody` como PROCESO EXTERNO.

    Nunca se importa ni se simula Java: el test/cliente solo habla TCP/JSON.
    Protecciones contra tests colgados: timeout de arranque, timeout de mensajes
    y terminacion limpia (terminate -> wait -> kill) del proceso.
    """

    def __init__(self, port: int, host: str = "127.0.0.1", telemetry: bool = True,
                 startup_timeout: float = 60.0) -> None:
        self.port = port
        self.host = host
        self.telemetry_enabled = telemetry
        self.startup_timeout = startup_timeout
        self._lines: list[str] = []
        self._lock = threading.Lock()
        self._proc: subprocess.Popen | None = None
        self._reader: threading.Thread | None = None
        self._command: list[str] = []

    @property
    def command(self) -> list[str]:
        return list(self._command)

    def start(self) -> None:
        java = java_executable() or "java"
        args = []
        if self.telemetry_enabled:
            args.append("-DHART_TELEMETRY=true")
        args += ["-cp", classpath(), "CharacterBody", str(self.port)]
        self._command = [java, *args]
        self._proc = subprocess.Popen(
            self._command,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self._reader = threading.Thread(target=self._pump, name="JavaBodyStdout", daemon=True)
        self._reader.start()

    def _pump(self) -> None:
        assert self._proc is not None and self._proc.stdout is not None
        for line in self._proc.stdout:
            with self._lock:
                self._lines.append(line.rstrip("\r\n"))

    def output(self) -> list[str]:
        with self._lock:
            return list(self._lines)

    def wait_for_line(self, needle: str, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if any(needle in line for line in self.output()):
                return True
            if self._proc is not None and self._proc.poll() is not None:
                return False  # el proceso murio antes de anunciarse
            time.sleep(0.05)
        return False

    def telemetry_rows(self) -> list[dict]:
        """Lineas `HART_TELEMETRY {...}` de stdout (canal independiente del protocolo)."""
        rows = []
        for line in self.output():
            if line.startswith(TELEMETRY_PREFIX):
                try:
                    rows.append(json.loads(line[len(TELEMETRY_PREFIX):]))
                except json.JSONDecodeError:
                    continue
        return rows

    @property
    def exit_code(self) -> int | None:
        return None if self._proc is None else self._proc.poll()

    @property
    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def stop(self, grace: float = 5.0, verify: bool = True) -> int | None:
        """Terminacion fiable: nunca dejar JVMs, ventanas ni puertos huerfanos.

        En Windows el `java.exe` lanzado puede ser un stub: se mata ademas el arbol
        del proceso y cualquier PID que siga escuchando en nuestro puerto, y se
        verifica que el puerto quedo cerrado.
        """
        if self._proc is None:
            return None

        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=grace)
            except subprocess.TimeoutExpired:
                self._kill_launched_process()

        if os.name == "nt":
            for pid in windows_pids_listening_on(self.port):
                self._taskkill(pid)

        if self._proc.poll() is None:
            self._kill_launched_process()

        if self._reader is not None:
            self._reader.join(timeout=grace)

        if verify and not wait_until_port_closed(self.host, self.port, timeout=grace):
            raise IntegrationError(
                f"no se pudo terminar la JVM que escuchaba en el puerto {self.port}: "
                "quedaria un proceso/ventana huerfano")

        return self._proc.poll()

    def _taskkill(self, pid: int) -> None:
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                           capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.SubprocessError):
            pass

    def _kill_launched_process(self) -> None:
        if self._proc is None:
            return
        if os.name == "nt":
            self._taskkill(self._proc.pid)
        else:
            self._proc.kill()
            try:
                self._proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                pass

    @property
    def stdout_closed(self) -> bool:
        return self._reader is not None and not self._reader.is_alive()

    def __enter__(self) -> "JavaBodyProcess":
        self.start()
        return self

    def __exit__(self, *_exc) -> None:
        self.stop(verify=False)  # la verificacion explicita la hace run_integration()


def _command_payload(orchestrator, perception: dict) -> dict:
    """Respuesta `command` construida con el orquestador REAL (mismas claves del protocolo)."""
    orchestrator.perceive_and_update(perception)
    thought, action = orchestrator.generate_internal_monologue()
    return {
        "type": "command",
        "sequence": perception.get("sequence"),
        "command": action,
        "thought": thought,
        "affectiveValence": orchestrator.state["affective_valence"],
        "affectiveMomentum": orchestrator.state["affective_momentum"],
        "agentState": orchestrator.compute_agent_state(),
        "motorOutput": orchestrator.compute_motor_output(),
        "sensorSensitivity": orchestrator.compute_sensor_sensitivity(),
    }


def _record_feedback(orchestrator, payload: dict, index: int) -> dict:
    """Aplica el feedback de Java y registra la telemetria que viaja en el protocolo."""
    orchestrator.apply_feedback(payload)
    return {
        "cycle": index,
        "sequence": payload.get("sequence"),
        "action_taken": payload.get("actionTaken"),
        "affective_change_java": payload.get("affectiveChange"),
        "saturation_factor": payload.get("saturationFactor"),
        "repeat_count": payload.get("repeatCount"),
        "switch_rate": payload.get("switchRate"),
        "rationale": payload.get("rationale"),
        "stdout_saturation_factor": "",
        "stdout_repeat_count": "",
        "stdout_switch_rate": "",
        "python_valence_after": round(orchestrator.state["affective_valence"], 6),
        "python_motor_output": round(orchestrator.compute_motor_output(), 6),
        "python_sensor_sensitivity": round(orchestrator.compute_sensor_sensitivity(), 6),
        "python_agent_state": orchestrator.compute_agent_state(),
    }


def _attach_stdout_telemetry(rows: list, telemetry_rows: list) -> None:
    """Cruza el canal de stdout con el del protocolo, posicion a posicion."""
    for index, row in enumerate(rows):
        if index >= len(telemetry_rows):
            break
        line = telemetry_rows[index]
        row["stdout_saturation_factor"] = line.get("saturationFactor")
        row["stdout_repeat_count"] = line.get("repeatCount")
        row["stdout_switch_rate"] = line.get("switchRate")


def run_integration(cycles: int = 10, host: str = "127.0.0.1", port: int | None = None,
                    startup_timeout: float = 60.0, message_timeout: float = 20.0,
                    telemetry: bool = True, quiet: bool = False,
                    keep_logs: bool = False) -> dict:
    """Ejecuta el sistema completo Python <-> Java y devuelve la evidencia registrada.

    Lanza `CharacterBody` como proceso externo, espera a que anuncie el servidor TCP,
    habla el protocolo hasta `cycles` feedbacks y termina Java de forma limpia
    (aunque falle a mitad: el `finally` garantiza la parada).
    """
    problems = environment_problems()
    if problems:
        raise EnvironmentNotReady("; ".join(problems))

    port = port or find_free_port(host)
    orchestrator = CognitiveOrchestrator(model_path=None)  # LLM off: dinamica programada
    rows: list[dict] = []
    exit_code: int | None = None
    telemetry_rows: list[dict] = []
    output: list[str] = []

    sink = contextlib.redirect_stdout(io.StringIO()) if quiet else contextlib.nullcontext()
    with JavaBodyProcess(port, host, telemetry, startup_timeout) as body:
        if not body.wait_for_line(BRIDGE_READY_MARKER, startup_timeout):
            tail = " | ".join(body.output()[-5:])
            raise IntegrationError(
                f"Java no anuncio el servidor TCP en {startup_timeout:.0f}s: {tail}")

        try:
            with sink:
                with socket.create_connection((host, port), timeout=startup_timeout) as sock:
                    sock.settimeout(message_timeout)
                    reader = sock.makefile("r", encoding="utf-8")
                    writer = sock.makefile("w", encoding="utf-8")
                    while len(rows) < cycles:
                        raw = reader.readline()
                        if not raw:
                            raise IntegrationError(
                                f"Java cerro la conexion tras {len(rows)}/{cycles} ciclos")
                        payload = json.loads(raw)
                        kind = payload.get("type")
                        if kind == "perception":
                            writer.write(json.dumps(
                                _command_payload(orchestrator, payload),
                                ensure_ascii=False) + "\n")
                            writer.flush()
                        elif kind == "feedback":
                            rows.append(_record_feedback(orchestrator, payload, len(rows) + 1))
                        else:
                            raise IntegrationError(f"tipo de mensaje desconocido: {kind!r}")
        except OSError as exc:
            tail = " | ".join(body.output()[-5:])
            raise IntegrationError(f"fallo TCP con el cuerpo Java: {exc} | {tail}") from exc
        finally:
            exit_code = body.stop()
            telemetry_rows = body.telemetry_rows()
            output = body.output()

    _attach_stdout_telemetry(rows, telemetry_rows)
    return {
        "status": "ok",
        "cycles": len(rows),
        "host": host,
        "port": port,
        "java_cmd": body.command,
        "java_exit_code": exit_code,
        "rows": rows,
        "telemetry_rows": telemetry_rows,
        "java_output_tail": output[-15:] if keep_logs else [],
    }


def validate_rows(rows: list) -> bool:
    """Falla (no skip) si la telemetria de Java no llego completa a Python."""
    if not rows:
        raise IntegrationError(
            "no se registro ningun feedback: el protocolo no completo ningun ciclo")

    for row in rows:
        cycle = row.get("cycle")
        factor = row.get("saturation_factor")
        if isinstance(factor, bool) or not isinstance(factor, (int, float)):
            raise IntegrationError(
                f"ciclo {cycle}: saturationFactor ausente en el protocolo Java (valor={factor!r})")
        if not SATURATION_MIN <= float(factor) <= SATURATION_MAX:
            raise IntegrationError(
                f"ciclo {cycle}: saturationFactor fuera de "
                f"[{SATURATION_MIN}, {SATURATION_MAX}]: {factor}")

        repeat = row.get("repeat_count")
        if isinstance(repeat, bool) or not isinstance(repeat, int) or repeat < 1:
            raise IntegrationError(f"ciclo {cycle}: repeatCount invalido: {repeat!r}")

        switch = row.get("switch_rate")
        if isinstance(switch, bool) or not isinstance(switch, (int, float)):
            raise IntegrationError(f"ciclo {cycle}: switchRate invalido: {switch!r}")
        if not 0.0 <= float(switch) <= 1.0:
            raise IntegrationError(f"ciclo {cycle}: switchRate fuera de [0, 1]: {switch}")

    return True


def telemetry_mismatches(rows: list, tolerance: float = 1e-4) -> list[str]:
    """Diferencias entre el canal del protocolo y la linea `HART_TELEMETRY` de stdout.

    Tolerancia 1e-4 porque Java formatea la linea de telemetria con 4 decimales.
    """
    problems = []
    for row in rows:
        cycle = row.get("cycle")
        observed = row.get("stdout_saturation_factor")
        if observed in ("", None):
            problems.append(f"ciclo {cycle}: sin linea HART_TELEMETRY para este feedback")
            continue
        if abs(float(observed) - float(row["saturation_factor"])) > tolerance:
            problems.append(
                f"ciclo {cycle}: saturationFactor protocolo={row['saturation_factor']} "
                f"stdout={observed}")
        if int(row.get("stdout_repeat_count")) != int(row["repeat_count"]):
            problems.append(
                f"ciclo {cycle}: repeatCount protocolo={row['repeat_count']} "
                f"stdout={row.get('stdout_repeat_count')}")
        if abs(float(row.get("stdout_switch_rate")) - float(row["switch_rate"])) > tolerance:
            problems.append(
                f"ciclo {cycle}: switchRate protocolo={row['switch_rate']} "
                f"stdout={row.get('stdout_switch_rate')}")
    return problems


def write_csv(rows: list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_summary(result: dict, path: Path) -> None:
    rows = result["rows"]
    factors = [float(row["saturation_factor"]) for row in rows]
    lines = [
        "# Integracion real Java <-> Python (Fase 3c)",
        "",
        f"- **Ciclos completados:** {result['cycles']}  |  **Puerto:** {result['port']}",
        f"- **Comando Java:** `{' '.join(result['java_cmd'])}`",
        f"- **Exit code del proceso Java:** {result['java_exit_code']}",
        "",
        "## Telemetria de saturacion recibida desde Java",
        "",
        f"- `saturationFactor`: min={min(factors):.4f}  max={max(factors):.4f}  "
        f"atenuados(<1.0)={sum(1 for f in factors if f < 1.0)}/{len(factors)}",
        f"- `repeatCount` maximo: {max(int(row['repeat_count']) for row in rows)}",
        f"- `switchRate` maximo: {max(float(row['switch_rate']) for row in rows):.4f}",
        f"- Lineas `HART_TELEMETRY` en stdout: {len(result['telemetry_rows'])}",
        "",
        "## Criterios de esta prueba",
        "",
        "```text",
        "display disponible  -> RUN",
        "display ausente     -> SKIP explicito (nunca pass silencioso)",
        "Java falla          -> FAIL",
        "TCP/protocolo falla -> FAIL",
        "telemetria ausente  -> FAIL",
        "```",
        "",
        "## Como reproducir",
        "",
        "```sh",
        f"python tools/run_integration.py --cycles {result['cycles']}",
        "python -m pytest tests/integration -q    # requiere JDK + display",
        "```",
        "",
        "## Regla de oro",
        "La dinamica proviene del `CognitiveOrchestrator` REAL y del `CharacterBody` REAL:",
        "esta ruta solo observa y registra el protocolo, no reescribe formulas.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Integracion real Java <-> Python (Fase 3c): comprueba que la telemetria "
                    "de saturacion que genera Java llega a Python.")
    parser.add_argument("--cycles", type=int, default=10)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0, help="0 = puerto libre automatico")
    parser.add_argument("--startup-timeout", type=float, default=60.0)
    parser.add_argument("--message-timeout", type=float, default=20.0)
    parser.add_argument("--no-telemetry-flag", action="store_true",
                        help="no pasar -DHART_TELEMETRY=true a la JVM")
    parser.add_argument("--out", default=str(RESULTS_DIR))
    args = parser.parse_args(argv)

    try:
        result = run_integration(
            cycles=args.cycles, host=args.host, port=args.port or None,
            startup_timeout=args.startup_timeout, message_timeout=args.message_timeout,
            telemetry=not args.no_telemetry_flag, keep_logs=True)
    except EnvironmentNotReady as exc:
        print(f"[ENTORNO] No se puede ejecutar la integracion: {exc}")
        return 3
    except IntegrationError as exc:
        print(f"[FALLO] Integracion incompleta: {exc}")
        return 2

    validate_rows(result["rows"])

    mismatches = telemetry_mismatches(result["rows"])
    if mismatches:
        print("[FALLO] El protocolo y la telemetria de stdout no coinciden:")
        for problem in mismatches:
            print(f"  - {problem}")
        return 2

    out_dir = Path(args.out) / f"tcp_{result['cycles']}cycles"
    write_csv(result["rows"], out_dir / "data.csv")
    write_summary(result, out_dir / "summary.md")

    factors = [float(row["saturation_factor"]) for row in result["rows"]]
    print(f"[OK] {result['cycles']} ciclos | puerto={result['port']} | "
          f"saturationFactor min={min(factors):.4f} max={max(factors):.4f} | "
          f"stdout_telemetry={len(result['telemetry_rows'])} lineas -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
