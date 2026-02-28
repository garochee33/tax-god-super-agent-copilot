from __future__ import annotations

from typing import List

from swarm.tools.shell import run_shell

RG_EXCLUDES = [
    "!.git/**",
    "!venv/**",
    "!liveportrait_venv/**",
    "!external_modules/**",
    "!output/**",
    "!backups/**",
    "!audit_archive/**",
    "!.mypy_cache/**",
    "!.pytest_cache/**",
    "!.ruff_cache/**",
]


def rg_command(pattern: str, path: str = ".") -> str:
    globs = " ".join([f"--glob '{g}'" for g in RG_EXCLUDES])
    return f"rg -n {pattern} -S {globs} {path}"


def run_offline_checks(repo_root, allowlist: List[str], commands: List[str]) -> str:
    outputs = []
    for cmd in commands:
        res = run_shell(cmd, repo_root, allowlist)
        header = f"$ {cmd} (exit {res.exit_code})"
        body = (res.stdout or "") + ("\n" + res.stderr if res.stderr else "")
        outputs.append(header + "\n" + body.strip())
    return "\n\n".join(outputs).strip()
