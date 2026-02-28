from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from git import Repo
import shutil
import subprocess
from typing import Optional


@dataclass
class Worktree:
    name: str
    path: Path
    branch: str


def _run_git(repo_root: str, args: list[str]) -> str:
    p = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{p.stderr}")
    return p.stdout


def capture_wip_patch(repo_root: str, out_path: Path) -> Optional[Path]:
    """
    Captures both unstaged and staged diffs into a single patch file.
    Returns patch path if there is any diff, else None.
    """
    unstaged = _run_git(repo_root, ["diff"])
    staged = _run_git(repo_root, ["diff", "--cached"])

    if not unstaged.strip() and not staged.strip():
        return None

    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined = ""
    if staged.strip():
        combined += staged
        if not combined.endswith("\n"):
            combined += "\n"
    if unstaged.strip():
        combined += unstaged
        if not combined.endswith("\n"):
            combined += "\n"

    out_path.write_text(combined, encoding="utf-8")
    return out_path


def apply_wip_patch(repo_root: str, worktree_path: Path, patch_path: Path) -> None:
    """
    Apply patch to a worktree. Uses 3-way merge fallback for resilience.
    """
    p = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", str(patch_path)],
        cwd=str(worktree_path),
        text=True,
        capture_output=True,
    )
    if p.returncode == 0:
        return

    p2 = subprocess.run(
        ["git", "apply", "--3way", "--whitespace=nowarn", str(patch_path)],
        cwd=str(worktree_path),
        text=True,
        capture_output=True,
    )
    if p2.returncode != 0:
        raise RuntimeError(
            f"Failed to apply WIP patch in {worktree_path}\n"
            f"git apply error:\n{p.stderr}\n---\n3way error:\n{p2.stderr}"
        )


def create_worktree(
    repo_root: str, workspace_dir: str, name: str, wip_patch: Optional[Path] = None
) -> Worktree:
    repo = Repo(repo_root)

    ws = Path(repo_root) / workspace_dir
    ws.mkdir(parents=True, exist_ok=True)

    branch = f"swarm/{name}"
    wt_path = ws / name

    if wt_path.exists():
        shutil.rmtree(wt_path, ignore_errors=True)

    if branch in [h.name for h in repo.heads]:
        repo.git.branch("-D", branch)

    repo.git.worktree("add", str(wt_path), "-b", branch)

    if wip_patch is not None:
        apply_wip_patch(repo_root, wt_path, wip_patch)

    return Worktree(name=name, path=wt_path, branch=branch)
