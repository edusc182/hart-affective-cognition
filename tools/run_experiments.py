#!/usr/bin/env python3
"""run_experiments.py - runner reproducible de experimentos.

Regla de oro: mide el sistema REAL; NO reimplementa la logica.
Importa CognitiveOrchestrator de orchestrator/orchestrator.py y le aplica un estímulo
reproducible declarado en experiments/configs/<name>.json. La dinamica (motor, sensibilidad,
valencia, momentum, habituacion) proviene del codigo real del orquestador.

Uso:
    python tools/run_experiments.py --experiment fear_response
    python tools/run_experiments.py --all
    python tools/run_experiments.py --all --no-plots
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "experiments" / "configs"
RESULTS_ROOT = ROOT / "experiments" / "results"
sys.path.insert(0, str(ROOT))

from orchestrator.orchestrator import CognitiveOrchestrator  # importa el MODELO REAL


def import_mpl():
    """Importa matplotlib de forma perezosa (opcional). El CSV siempre disponible."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except Exception:
        return None


# Nota: `saturation_factor` es telemetria de Java (Fase 3d/3c); en modo orquestador-puro
# (sin Java) la columna se deja vacia.
COLUMNS = [
    "cycle", "timestamp", "sequence", "light_level", "distance", "current_action",
    "affective_valence", "affective_momentum", "motor_output", "sensor_sensitivity",
    "agent_state", "direct_affective_change", "effective_affective_change",
    "historical_inertia", "repeat_count", "switch_rate", "saturation_factor",
    "thought", "rationale",
]


@contextlib.contextmanager
def silenced():
    """Suprime los prints internos del orquestador durante la simulacion."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield buf


def load_config(name: str) -> dict:
    path = CONFIG_DIR / f"{name}.json"
    if not path.exists():
        raise SystemExit(f"[ERROR] Config no encontrado: {path}")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def observational_metrics(actions: list) -> tuple:
    """Cuenta de forma OBSERVACIONAL: repeticiones consecutivas y switch-rate.
    NO reimplementa computeSaturationFactor; solo observa la secuencia de acciones."""
    a = actions[-1]
    repeat_count = 1
    for prev in reversed(actions[:-1]):
        if prev == a:
            repeat_count += 1
        else:
            break
    transitions = 0
    for i in range(1, len(actions)):
        if actions[i] != actions[i - 1]:
            transitions += 1
    switch_rate = transitions / (len(actions) - 1) if len(actions) > 1 else 0.0
    return repeat_count, switch_rate


def run_experiment(cfg: dict):
    random.seed(cfg.get("seed", 0))
    orch = CognitiveOrchestrator(model_path=None)  # llm disabled -> heuristic_response()
    st = orch.state
    init = cfg.get("initial_state", {})
    st["affective_valence"] = float(init.get("affective_valence", st["affective_valence"]))
    st["affective_momentum"] = 0.0
    orch.cycles_in_comfort = 0
    st["current_action"] = "INACTIVO"

    stim = cfg["stimulus"]
    lights = stim["light_level"]
    dists = stim["distance"]
    deltas = stim["affective_change"]
    n = int(cfg.get("cycles", len(lights)))

    rows = []
    actions = []
    start = time.time()
    for i in range(n):
        light = lights[i]
        dist = float(dists[i])
        delta = float(deltas[i])
        seq = i + 1
        sensory = {
            "lightLevel": light,
            "proximityToObjectMeters": dist,
            "currentAction": st.get("current_action", "INACTIVO"),
            "sequence": seq,
        }
        with silenced():
            orch.perceive_and_update(sensory)
            thought, action = orch.generate_internal_monologue()
            orch.apply_feedback({
                "actionTaken": action,
                "affectiveChange": delta,
                "rationale": "simulated stimulus feedback (Java evaluateAffectiveFeedback)",
                "sequence": seq,
            })

        motor = orch.compute_motor_output()
        sens = orch.compute_sensor_sensitivity()
        astate = orch.compute_agent_state()
        mem = st["memory_shortterm"][-1] if st["memory_shortterm"] else {}
        actions.append(action)
        rc, sw = observational_metrics(actions)
        rows.append({
            "cycle": seq,
            "timestamp": round(time.time() - start, 4),
            "sequence": mem.get("sequence", seq),
            "light_level": light,
            "distance": dist,
            "current_action": action,
            "affective_valence": round(st["affective_valence"], 4),
            "affective_momentum": round(mem.get("historicalInertia", 0.0), 4),
            "motor_output": round(motor, 4),
            "sensor_sensitivity": round(sens, 4),
            "agent_state": astate,
            "direct_affective_change": round(mem.get("directAffectiveChange", delta), 4),
            "effective_affective_change": round(mem.get("effectiveAffectiveChange", delta), 4),
            "historical_inertia": round(mem.get("historicalInertia", 0.0), 4),
            "repeat_count": rc,
            "switch_rate": round(sw, 4),
            "saturation_factor": "",
            "thought": thought,
            "rationale": mem.get("rationale", ""),
        })
        st["current_action"] = action
    return rows


def write_csv(rows: list, path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_summary(cfg: dict, rows: list, path: Path) -> None:
    last = rows[-1]
    init = cfg.get("initial_state", {})
    lines = [
        f"# Resultado del experimento: {cfg['name']}",
        "",
        f"- **Categoría:** {cfg.get('category', '')}",
        f"- **LLM:** {cfg.get('llm', 'disabled')}  |  **Seed:** {cfg.get('seed', '')}",
        f"- **Ciclos:** {cfg.get('cycles', len(rows))}",
        f"- **Initial state:** valencia = {init.get('affective_valence')}, "
        f"momentum = {init.get('affective_momentum')}",
        "",
        "## Trayectoria (último ciclo)",
        f"- valence: {last['affective_valence']:+.3f}",
        f"- momentum: {last['affective_momentum']:+.3f}",
        f"- motor_output: {last['motor_output']:.3f}",
        f"- sensor_sensitivity: {last['sensor_sensitivity']:.3f}",
        f"- agent_state: {last['agent_state']}",
        f"- repeat_count: {last['repeat_count']}  |  switch_rate: {last['switch_rate']}",
        "- saturation_factor: NA (telemetría Java, Fase 3d/3c) — no disponible en modo orquestador-puro.",
        "",
        "## Cómo reproducir",
        "```sh",
        "python tools/run_experiments.py --experiment " + cfg["name"],
        "```",
        "Los CSV son deterministas: mismo seed + la misma config reproducen los datos.",
        "",
        "## Regla de oro",
        "Estos datos provienen del CognitiveOrchestrator REAL. La dinámica no fue reescrita.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_plots(rows: list, out_dir: Path, name: str) -> bool:
    plt = import_mpl()
    if plt is None:
        return False
    cycles = [r["cycle"] for r in rows]
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax1 = axes[0]
    ax1.plot(cycles, [r["affective_valence"] for r in rows], marker="o", label="valence")
    ax1.plot(cycles, [r["affective_momentum"] for r in rows], marker="s", label="momentum")
    ax1.axhline(0, color="k", lw=0.5)
    ax1.set_ylabel("affective state")
    ax1.set_title(f"{name} - afecto")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2 = axes[1]
    ax2.plot(cycles, [r["motor_output"] for r in rows], marker="o", label="motor_output")
    ax2.set_ylabel("motor_output", color="tab:blue")
    ax2b = ax2.twinx()
    ax2b.plot(cycles, [r["sensor_sensitivity"] for r in rows], marker="s",
              color="tab:orange", label="sensor_sensitivity")
    ax2b.set_ylabel("sensor_sensitivity", color="tab:orange")
    ax2.set_xlabel("cycle")
    ax2.set_title("paradoja emocional: motor (descenso miedo) vs sensibilidad (ascenso miedo)")
    ax2.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(plots_dir / "valence.png", dpi=110)
    plt.close(fig)

    fig2, ax = plt.subplots(figsize=(8, 3))
    states = [r["agent_state"] for r in rows]
    for i, s in enumerate(states):
        ax.scatter(i + 1, 0, s=140)
        ax.text(i + 1, 0, f"{s}\n[{rows[i]['current_action']}]", rotation=30,
                ha="right", va="top", fontsize=7)
    ax.set_yticks([])
    ax.set_xlabel("cycle")
    ax.set_title("timeline - agent_state / accion")
    ax.set_xticks(cycles)
    fig2.tight_layout()
    fig2.savefig(plots_dir / "behavior.png", dpi=110)
    plt.close(fig2)
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Runner reproducible de experimentos sobre CognitiveOrchestrator.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--experiment", help="nombre del experimento (en experiments/configs/<name>.json)")
    g.add_argument("--all", action="store_true", help="ejecuta todos los experimentos")
    ap.add_argument("--no-plots", action="store_true", help="no genera PNGs (solo CSV + summary)")
    args = ap.parse_args(argv)

    gen_plots = not args.no_plots
    cfgs = (sorted(CONFIG_DIR.glob("*.json")) if args.all
            else [CONFIG_DIR / f"{args.experiment}.json"])
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)

    for cp in cfgs:
        cfg = json.loads(cp.read_text(encoding="utf-8"))
        name = cfg["name"]
        out = RESULTS_ROOT / name
        out.mkdir(parents=True, exist_ok=True)
        (out / "config.json").write_text(
            json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        rows = run_experiment(cfg)
        write_csv(rows, out / "data.csv")
        write_summary(cfg, rows, out / "summary.md")
        plotted = render_plots(rows, out, name) if gen_plots else False
        last = rows[-1]
        print(f"[{name}] cycles={len(rows)} "
              f"valence_final={last['affective_valence']:+.3f} "
              f"motor={last['motor_output']:.3f} "
              f"sensor={last['sensor_sensitivity']:.3f} "
              f"plots={'yes' if plotted else 'no'} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
