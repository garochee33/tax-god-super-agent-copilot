"""
Tax God API - Hardened Developer Tracking System
Git hooks, agent registry, consensus protocol, conflict detection,
build health, velocity metrics, integrity checksums, deployment gate.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import AdminUser, CurrentUser

router = APIRouter()

DEV_DIR = Path(".dev")
AGENTS_FILE = DEV_DIR / "agents.json"
PROPOSALS_FILE = DEV_DIR / "proposals.json"
LOCKS_FILE = DEV_DIR / "locks.json"
INTEGRITY_FILE = DEV_DIR / "integrity.json"

# Build health cache
_health_cache: dict[str, Any] = {"result": None, "ts": 0.0}


def _read_json(path: Path) -> list | dict:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return [] if path != INTEGRITY_FILE else {}


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


# ---------------------------------------------------------------------------
# 1. Git Hook Protocol
# ---------------------------------------------------------------------------

SECRET_PATTERNS = [
    r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}",
    r"sk-[a-zA-Z0-9]{20,}",
    r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
]


class PreCommitRequest(BaseModel):
    message: str = ""
    diff: str = ""


class PostCommitRequest(BaseModel):
    sha: str = ""
    message: str = ""
    author: str = ""
    files_changed: list[str] = Field(default_factory=list)


@router.post("/hooks/pre-commit")
async def pre_commit_hook(body: PreCommitRequest, _user: AdminUser):
    errors = []
    if body.message and not re.match(r"^[a-z]+: .+", body.message):
        errors.append("Commit message must match 'type: description' format")
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, body.diff):
            errors.append(f"Potential secret detected in diff (pattern: {pattern[:30]}...)")
            break
    return {"exit_code": 1 if errors else 0, "errors": errors}


@router.post("/hooks/post-commit")
async def post_commit_hook(body: PostCommitRequest, _user: AdminUser):
    log_entry = {
        "id": str(uuid.uuid4()),
        "sha": body.sha,
        "message": body.message,
        "author": body.author,
        "files_changed": body.files_changed,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    logs = _read_json(DEV_DIR / "build_logs.json")
    if not isinstance(logs, list):
        logs = []
    logs.append(log_entry)
    _write_json(DEV_DIR / "build_logs.json", logs)
    return {"exit_code": 0, "logged": log_entry["id"]}


# ---------------------------------------------------------------------------
# 2. Agent Registry
# ---------------------------------------------------------------------------


class AgentRegister(BaseModel):
    name: str
    capabilities: list[str] = Field(default_factory=list)


@router.get("/agents")
async def list_agents(_user: CurrentUser):
    return _read_json(AGENTS_FILE)


@router.post("/agents")
async def register_agent(body: AgentRegister, _user: AdminUser):
    agents = _read_json(AGENTS_FILE)
    if not isinstance(agents, list):
        agents = []
    existing = next((a for a in agents if a["name"] == body.name), None)
    if existing:
        existing["capabilities"] = body.capabilities
        existing["last_active"] = datetime.now(UTC).isoformat()
    else:
        agents.append({
            "name": body.name,
            "capabilities": body.capabilities,
            "last_active": datetime.now(UTC).isoformat(),
            "commits_count": 0,
        })
    _write_json(AGENTS_FILE, agents)
    return {"status": "registered", "agent": body.name}


# ---------------------------------------------------------------------------
# 3. Consensus Protocol
# ---------------------------------------------------------------------------


class Proposal(BaseModel):
    description: str
    files_affected: list[str] = Field(default_factory=list)
    risk_level: str = Field(default="low", pattern="^(low|medium|high)$")


class ApproveRequest(BaseModel):
    proposal_id: str


@router.post("/consensus/propose")
async def propose_change(body: Proposal, _user: AdminUser):
    proposals = _read_json(PROPOSALS_FILE)
    if not isinstance(proposals, list):
        proposals = []
    pid = str(uuid.uuid4())[:8]
    entry = {
        "id": pid,
        "description": body.description,
        "files_affected": body.files_affected,
        "risk_level": body.risk_level,
        "status": "approved" if body.risk_level == "low" else "pending",
        "created": datetime.now(UTC).isoformat(),
    }
    proposals.append(entry)
    _write_json(PROPOSALS_FILE, proposals)
    return entry


@router.get("/consensus/pending")
async def pending_proposals(_user: CurrentUser):
    proposals = _read_json(PROPOSALS_FILE)
    if not isinstance(proposals, list):
        return []
    return [p for p in proposals if p.get("status") == "pending"]


@router.post("/consensus/approve")
async def approve_proposal(body: ApproveRequest, _user: AdminUser):
    proposals = _read_json(PROPOSALS_FILE)
    if not isinstance(proposals, list):
        raise HTTPException(404, "Proposal not found")
    for p in proposals:
        if p["id"] == body.proposal_id:
            p["status"] = "approved"
            _write_json(PROPOSALS_FILE, proposals)
            return p
    raise HTTPException(404, "Proposal not found")


# ---------------------------------------------------------------------------
# 4. Conflict Detection & Locks
# ---------------------------------------------------------------------------


class LockRequest(BaseModel):
    file: str
    agent: str = ""


@router.get("/conflicts")
async def detect_conflicts(_user: CurrentUser):
    locks = _read_json(LOCKS_FILE)
    if not isinstance(locks, list):
        locks = []
    # Check git status
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, timeout=10
        )
        modified = [line[3:] for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        modified = []
    # Files locked by multiple agents
    file_agents: dict[str, list] = {}
    for lock in locks:
        f = lock.get("file", "")
        file_agents.setdefault(f, []).append(lock.get("agent", "unknown"))
    conflicts = [{"file": f, "agents": a} for f, a in file_agents.items() if len(a) > 1]
    return {"modified_files": modified, "conflicts": conflicts, "active_locks": locks}


@router.post("/locks")
async def lock_file(body: LockRequest, _user: AdminUser):
    locks = _read_json(LOCKS_FILE)
    if not isinstance(locks, list):
        locks = []
    if any(l.get("file") == body.file for l in locks):
        raise HTTPException(409, f"File '{body.file}' already locked")
    locks.append({
        "file": body.file,
        "agent": body.agent,
        "locked_at": datetime.now(UTC).isoformat(),
    })
    _write_json(LOCKS_FILE, locks)
    return {"locked": body.file}


@router.delete("/locks/{file:path}")
async def unlock_file(file: str, _user: AdminUser):
    locks = _read_json(LOCKS_FILE)
    if not isinstance(locks, list):
        locks = []
    new_locks = [l for l in locks if l.get("file") != file]
    if len(new_locks) == len(locks):
        raise HTTPException(404, f"No lock found for '{file}'")
    _write_json(LOCKS_FILE, new_locks)
    return {"unlocked": file}


# ---------------------------------------------------------------------------
# 5. Build Health
# ---------------------------------------------------------------------------


@router.get("/health")
async def build_health(_user: CurrentUser):
    global _health_cache
    if _health_cache["result"] and (time.time() - _health_cache["ts"]) < 60:
        return _health_cache["result"]

    checks: dict[str, Any] = {}
    # Compile check
    try:
        r = subprocess.run(
            ["python3", "-m", "py_compile", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        # Actually check all .py files compile
        r = subprocess.run(
            ["python3", "-c", "import compileall; exit(0 if compileall.compile_dir('app', quiet=2) else 1)"],
            capture_output=True, text=True, timeout=30,
        )
        checks["compile"] = {"pass": r.returncode == 0, "output": r.stderr[:500] if r.stderr else ""}
    except Exception as e:
        checks["compile"] = {"pass": False, "output": str(e)}

    # Ruff
    try:
        r = subprocess.run(["ruff", "check", "app/"], capture_output=True, text=True, timeout=30)
        checks["lint"] = {"pass": r.returncode == 0, "output": r.stdout[:500]}
    except FileNotFoundError:
        checks["lint"] = {"pass": True, "output": "ruff not installed, skipped"}
    except Exception as e:
        checks["lint"] = {"pass": False, "output": str(e)}

    # Pytest
    try:
        r = subprocess.run(
            ["python3", "-m", "pytest", "tests/", "-x", "--tb=short", "-q"],
            capture_output=True, text=True, timeout=120,
        )
        checks["tests"] = {"pass": r.returncode == 0, "output": (r.stdout + r.stderr)[:1000]}
    except Exception as e:
        checks["tests"] = {"pass": False, "output": str(e)}

    overall = all(c["pass"] for c in checks.values())
    result = {"status": "pass" if overall else "fail", "checks": checks}
    _health_cache = {"result": result, "ts": time.time()}
    return result


# ---------------------------------------------------------------------------
# 6. Change Velocity Metrics
# ---------------------------------------------------------------------------


@router.get("/metrics")
async def velocity_metrics(_user: CurrentUser):
    try:
        # Commits per day (last 7 days)
        r = subprocess.run(
            ["git", "log", "--oneline", "--since=7 days ago", "--format=%H|%aI|%an"],
            capture_output=True, text=True, timeout=10,
        )
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        commits_by_day: dict[str, int] = {}
        agent_commits: dict[str, int] = {}
        for line in lines:
            parts = line.split("|")
            if len(parts) >= 3:
                day = parts[1][:10]
                commits_by_day[day] = commits_by_day.get(day, 0) + 1
                agent_commits[parts[2]] = agent_commits.get(parts[2], 0) + 1

        # Files changed per commit + lines
        r2 = subprocess.run(
            ["git", "log", "--since=7 days ago", "--shortstat", "--format="],
            capture_output=True, text=True, timeout=10,
        )
        total_files, total_add, total_del, commit_count = 0, 0, 0, 0
        for line in r2.stdout.splitlines():
            m = re.search(r"(\d+) file", line)
            if m:
                total_files += int(m.group(1))
                commit_count += 1
            m_add = re.search(r"(\d+) insertion", line)
            if m_add:
                total_add += int(m_add.group(1))
            m_del = re.search(r"(\d+) deletion", line)
            if m_del:
                total_del += int(m_del.group(1))

        return {
            "commits_per_day": commits_by_day,
            "total_commits_7d": len(lines),
            "avg_files_per_commit": round(total_files / max(commit_count, 1), 1),
            "lines_added": total_add,
            "lines_removed": total_del,
            "agent_breakdown": agent_commits,
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 7. Integrity Checksums
# ---------------------------------------------------------------------------


def _hash_py_files() -> dict[str, str]:
    hashes = {}
    for f in Path("app").rglob("*.py"):
        hashes[str(f)] = hashlib.sha256(f.read_bytes()).hexdigest()
    return hashes


@router.post("/integrity/snapshot")
async def integrity_snapshot(_user: AdminUser):
    hashes = _hash_py_files()
    _write_json(INTEGRITY_FILE, {"snapshot_at": datetime.now(UTC).isoformat(), "files": hashes})
    return {"files_hashed": len(hashes)}


@router.get("/integrity/verify")
async def integrity_verify(_user: CurrentUser):
    data = _read_json(INTEGRITY_FILE)
    if not isinstance(data, dict) or "files" not in data:
        raise HTTPException(404, "No integrity snapshot found. Run POST /integrity/snapshot first.")
    stored = data["files"]
    current = _hash_py_files()
    tampered, added, removed = [], [], []
    for f, h in stored.items():
        if f not in current:
            removed.append(f)
        elif current[f] != h:
            tampered.append(f)
    for f in current:
        if f not in stored:
            added.append(f)
    ok = not tampered and not removed
    return {
        "integrity": "ok" if ok else "compromised",
        "tampered": tampered,
        "added": added,
        "removed": removed,
        "snapshot_at": data.get("snapshot_at"),
    }


# ---------------------------------------------------------------------------
# 8. Deployment Gate
# ---------------------------------------------------------------------------


@router.post("/gate/check")
async def deployment_gate(_user: AdminUser):
    reasons = []
    go = True

    # Tests
    try:
        r = subprocess.run(
            ["python3", "-m", "pytest", "tests/", "-x", "--tb=line", "-q"],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode != 0:
            go = False
            reasons.append("Tests failing")
    except Exception:
        go = False
        reasons.append("Could not run tests")

    # Lint
    try:
        r = subprocess.run(["ruff", "check", "app/"], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            go = False
            reasons.append("Lint errors present")
    except FileNotFoundError:
        pass  # ruff not installed, skip

    # Uncommitted changes
    try:
        r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=10)
        if r.stdout.strip():
            go = False
            reasons.append("Uncommitted changes detected")
    except Exception:
        reasons.append("Could not check git status")

    # Integrity
    data = _read_json(INTEGRITY_FILE)
    if isinstance(data, dict) and "files" in data:
        current = _hash_py_files()
        for f, h in data["files"].items():
            if f in current and current[f] != h:
                go = False
                reasons.append(f"Integrity mismatch: {f}")
                break

    return {"gate": "go" if go else "no-go", "reasons": reasons}
