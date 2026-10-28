"""Declarative scenario definitions (scenarios/*.yaml)."""
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ACTORS = {"inject", "auto", "human", "runbook"}


class ScenarioError(ValueError):
    pass


@dataclass
class Step:
    name: str
    action: str
    actor: str
    args: dict = field(default_factory=dict)


@dataclass
class Scenario:
    id: str
    title: str
    tier: str
    description: str
    targets: dict
    fault: list
    runbook: list
    warmup_s: float | None = None
    max_duration_s: float = 900
    path: Path | None = None


def _steps(raw, section, default_actor, known_actions, src):
    if not isinstance(raw, list) or not raw:
        raise ScenarioError(f"{src}: '{section}' must be a non-empty list")
    steps = []
    for i, s in enumerate(raw):
        where = f"{src}: {section}[{i}]"
        if not isinstance(s, dict) or "action" not in s or "name" not in s:
            raise ScenarioError(f"{where} needs 'name' and 'action'")
        args = {k: v for k, v in s.items() if k not in ("name", "action", "actor")}
        actor = s.get("actor", default_actor)
        if actor not in ACTORS:
            raise ScenarioError(f"{where}: unknown actor '{actor}'")
        if s["action"] not in known_actions:
            raise ScenarioError(f"{where}: unknown action '{s['action']}' "
                                f"(provider supports: {', '.join(sorted(known_actions))})")
        steps.append(Step(s["name"], s["action"], actor, args))
    return steps


def load(path, known_actions):
    path = Path(path)
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict):
        raise ScenarioError(f"{path}: not a mapping")
    missing = {"id", "title", "tier", "targets", "fault", "runbook"} - raw.keys()
    if missing:
        raise ScenarioError(f"{path}: missing {', '.join(sorted(missing))}")
    t = raw["targets"]
    if not isinstance(t, dict) or not {"rto_s", "rpo_s"} <= t.keys():
        raise ScenarioError(f"{path}: targets need rto_s and rpo_s")
    return Scenario(
        id=raw["id"], title=raw["title"], tier=raw["tier"],
        description=" ".join(str(raw.get("description", "")).split()),
        targets=t,
        fault=_steps(raw["fault"], "fault", "inject", known_actions, path),
        runbook=_steps(raw["runbook"], "runbook", "runbook", known_actions, path),
        warmup_s=raw.get("warmup_s"),
        max_duration_s=raw.get("max_duration_s", 900),
        path=path,
    )


def load_dir(directory, known_actions):
    return {s.id: s for s in (load(p, known_actions) for p in sorted(Path(directory).glob("*.yaml")))}
