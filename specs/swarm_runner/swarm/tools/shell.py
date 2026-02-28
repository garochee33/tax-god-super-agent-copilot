from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class ShellResult:
    exit_code: int
    stdout: str
    stderr: str


def _is_allowed(command: str, allowlist: List[str]) -> bool:
    command = command.strip()
    for allowed in allowlist:
        if command == allowed or command.startswith(allowed + " "):
            return True
    return False


def run_shell(command: str, cwd: Path, allowlist: List[str]) -> ShellResult:
    if not _is_allowed(command, allowlist):
        return ShellResult(1, "", f"Blocked by allowlist: {command}")
    cmd = shlex.split(command)
    try:
        p = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)
        return ShellResult(p.returncode, p.stdout, p.stderr)
    except FileNotFoundError:
        return ShellResult(1, "", f"Command not found: {cmd[0]}")
