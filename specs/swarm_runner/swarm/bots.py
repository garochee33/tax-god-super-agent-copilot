from __future__ import annotations

from dataclasses import dataclass
from typing import List

from swarm.tools.offline import rg_command


@dataclass(frozen=True)
class BotSpec:
    name: str
    role: str
    description: str
    offline_checks: List[str]


def default_bots() -> List[BotSpec]:
    return [
        BotSpec(
            name="architect",
            role="ARCHITECT",
            description="System design, architecture, and repo understanding.",
            offline_checks=[
                rg_command("\"ARCHITECT|DESIGN|ADR|RFC|diagram|architecture\""),
                rg_command("\"README|docs|docs/|design\""),
            ],
        ),
        BotSpec(
            name="feature",
            role="FEATURE",
            description="Feature ideation, scope, and MVP planning.",
            offline_checks=[
                rg_command("\"main\\(|entry|CLI|GUI\""),
                rg_command("\"TODO|FEATURE|ROADMAP\""),
            ],
        ),
        BotSpec(
            name="implementer",
            role="IMPLEMENTER",
            description="Implementation plan and patch generation.",
            offline_checks=[
                "git status",
                rg_command("\"TODO|IMPLEMENT|FEATURE|MVP|P0\""),
            ],
        ),
        BotSpec(
            name="refactor",
            role="REFACTOR",
            description="Maintainability, cleanup, and structure improvements.",
            offline_checks=[
                rg_command("\"REFACTOR|cleanup|debt\""),
                rg_command("\"TODO|FIXME|HACK\""),
            ],
        ),
        BotSpec(
            name="bugfix",
            role="BUGFIX",
            description="Bug detection and fixes.",
            offline_checks=[
                "git status",
                rg_command("\"TODO|FIXME|BUG|ERROR|Traceback\""),
            ],
        ),
        BotSpec(
            name="debugger",
            role="DEBUGGER",
            description="Failure analysis and diagnostics.",
            offline_checks=[
                rg_command("\"Traceback|Exception|panic|stack trace\""),
                rg_command("\"FIXME|BUG|ERROR\""),
            ],
        ),
        BotSpec(
            name="tests",
            role="TESTS",
            description="Test planning and coverage improvements.",
            offline_checks=[
                rg_command("\"pytest|unittest|jest|mocha|vitest|go test\""),
                rg_command("\"TODO|test|coverage\""),
            ],
        ),
        BotSpec(
            name="optimizer",
            role="OPTIMIZER",
            description="Performance and efficiency analysis.",
            offline_checks=[
                rg_command("\"perf|performance|benchmark|latency|slow|optimi|cache\""),
                rg_command("\"TODO|FIXME|HACK|hot path\""),
            ],
        ),
        BotSpec(
            name="security",
            role="SECURITY",
            description="Security posture and vulnerabilities.",
            offline_checks=[
                rg_command("\"auth|token|password|secret|key|crypto\""),
                rg_command("\"OWASP|CVE|vulnerab|sanitize\""),
            ],
        ),
        BotSpec(
            name="docs",
            role="DOCS",
            description="Documentation and developer onboarding.",
            offline_checks=[
                rg_command("\"README|docs|documentation|guide\""),
                rg_command("\"TODO|DOCS\""),
            ],
        ),
        BotSpec(
            name="reasoner",
            role="REASONER",
            description="Fractal Reasoner: deep cognition, chain-of-thought, multi-step inference.",
            offline_checks=[
                rg_command("\"logic|reason|proof|infer|derive\""),
                rg_command("\"TODO|FIXME|design decision\""),
            ],
        ),
        BotSpec(
            name="teacher",
            role="TEACHER",
            description="Teacher: explanations, curricula, onboarding.",
            offline_checks=[
                rg_command("\"README|tutorial|guide|howto|explain\""),
                rg_command("\"TODO|DOCS|onboarding\""),
            ],
        ),
    ]


def build_bots(custom_specs: List[dict]) -> List[BotSpec]:
    if not custom_specs:
        return default_bots()
    specs: List[BotSpec] = []
    for raw in custom_specs:
        name = str(raw.get("name", "")).strip()
        role = str(raw.get("role", "")).strip()
        if not name or not role:
            continue
        description = str(raw.get("description", "")).strip() or f"{name} bot."
        offline_checks = [str(item) for item in raw.get("offline_checks", [])]
        specs.append(
            BotSpec(
                name=name,
                role=role,
                description=description,
                offline_checks=offline_checks,
            )
        )
    return specs or default_bots()
