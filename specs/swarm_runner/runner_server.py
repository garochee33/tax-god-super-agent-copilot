from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Portable: swarm repo root = directory containing this script
SWARM_DIR = Path(__file__).resolve().parent
# Default repo for /run: env AGENT_SWARM_DEFAULT_REPO or current working dir of server
DEFAULT_REPO = os.environ.get("AGENT_SWARM_DEFAULT_REPO", str(Path.cwd()))


def _read_json_file(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _parse_bool_env(name: str, default: bool = False) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return default


def _safe_workspace_id(value: str) -> str:
    raw = (value or "").strip()
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", raw).strip("._-")
    return safe[:64]


def _resolve_workspace_context(
    headers: Any, payload: dict
) -> Tuple[Optional[str], Optional[str]]:
    # Prefer headers; allow body as fallback for simple clients.
    workspace_id = headers.get("x-workspace-id") or payload.get("workspaceId")
    user_id = (
        headers.get("x-user-id")
        or headers.get("x-investor-id")
        or payload.get("userId")
    )
    if workspace_id:
        workspace_id = _safe_workspace_id(str(workspace_id))
    if user_id:
        user_id = str(user_id).strip()
    return (workspace_id or None, user_id or None)


def _check_acl(workspace_id: str, user_id: str, repo: str) -> Tuple[bool, str]:
    """
    Optional local ACL file (JSON). When enabled, requires:
      - workspace exists
      - user is in members/admins
      - repo is allowed (if repos list present)

    Format:
    {
      "workspaces": {
        "ws_123": {
          "members": ["user_a"],
          "admins": ["user_admin"],
          "repos": ["/abs/path/to/repo"]
        }
      }
    }
    """
    acl_path = os.environ.get("AGENT_SWARM_ACL_PATH")
    if not acl_path:
        return (False, "AGENT_SWARM_ACL_PATH not set")
    data = _read_json_file(Path(acl_path).expanduser())
    ws = ((data.get("workspaces") or {}).get(workspace_id)) if isinstance(data, dict) else None
    if not isinstance(ws, dict):
        return (False, "Workspace access denied")
    members = ws.get("members") if isinstance(ws.get("members"), list) else []
    admins = ws.get("admins") if isinstance(ws.get("admins"), list) else []
    allowed_users = {str(u) for u in (members + admins)}
    if user_id not in allowed_users:
        return (False, "Workspace access denied")
    repos = ws.get("repos") if isinstance(ws.get("repos"), list) else None
    if repos:
        allowed_repos = {str(r) for r in repos}
        if str(repo) not in allowed_repos:
            return (False, "Repo access denied")
    return (True, "ok")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_sse_headers(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

    def _sse_event(self, event: str, payload: dict) -> bool:
        try:
            data = json.dumps(payload, ensure_ascii=False)
            msg = f"event: {event}\ndata: {data}\n\n"
            self.wfile.write(msg.encode("utf-8"))
            self.wfile.flush()
            return True
        except Exception:
            return False

    def do_GET(self):
        # Streaming run output (SSE): /run/stream?goal=...&repoRoot=...
        if not self.path.startswith("/run/stream"):
            return self._send(404, {"error": "not found"})

        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        goal = (qs.get("goal", [""])[0] or "").strip()
        repo = (qs.get("repoRoot", [""])[0] or "").strip() or DEFAULT_REPO
        if not goal:
            return self._send(400, {"error": "goal is required"})

        enforce_acl = _parse_bool_env("ENFORCE_WORKSPACE_ACL", default=False)
        payload = {"goal": goal, "repoRoot": repo}
        workspace_id, user_id = _resolve_workspace_context(self.headers, payload)
        if enforce_acl:
            if not workspace_id or not user_id:
                return self._send(401, {"error": "Missing workspace context"})
            ok, msg = _check_acl(workspace_id, user_id, str(repo))
            if not ok:
                if msg == "AGENT_SWARM_ACL_PATH not set":
                    return self._send(500, {"error": msg})
                return self._send(403, {"error": msg})

        self._send_sse_headers()
        self._sse_event(
            "start",
            {"goal": goal, "repoRoot": repo, "workspaceId": workspace_id, "userId": user_id},
        )

        cmd = ["python3", "-m", "swarm.cli", "run", "--repo", repo, "--goal", goal]
        env: Dict[str, str] = dict(os.environ)
        if workspace_id:
            env["AGENT_SWARM_WORKSPACE_SUBDIR"] = workspace_id

        proc = subprocess.Popen(
            cmd,
            cwd=str(SWARM_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            bufsize=1,
        )

        artifacts_path: Optional[str] = None
        try:
            import selectors

            sel = selectors.DefaultSelector()
            if proc.stdout:
                sel.register(proc.stdout, selectors.EVENT_READ, data="stdout")
            if proc.stderr:
                sel.register(proc.stderr, selectors.EVENT_READ, data="stderr")

            while True:
                if proc.poll() is not None and not sel.get_map():
                    break
                events = sel.select(timeout=0.2)
                for key, _mask in events:
                    stream_name = key.data
                    f = key.fileobj
                    line = f.readline()
                    if not line:
                        try:
                            sel.unregister(f)
                        except Exception:
                            pass
                        continue
                    if stream_name == "stdout":
                        m = re.search(r"^Artifacts:\\s+(?P<path>.+)$", line)
                        if m:
                            artifacts_path = m.group("path").strip()
                    ok = self._sse_event(stream_name, {"line": line.rstrip("\n")})
                    if not ok:
                        proc.terminate()
                        return
        finally:
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()

        self._sse_event(
            "done",
            {
                "ok": proc.returncode == 0,
                "code": proc.returncode,
                "artifactsPath": artifacts_path,
            },
        )

    def do_POST(self):
        if self.path != "/run":
            return self._send(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            payload = {}
        goal = payload.get("goal")
        repo = payload.get("repoRoot") or DEFAULT_REPO
        if not goal:
            return self._send(400, {"error": "goal is required"})

        enforce_acl = _parse_bool_env("ENFORCE_WORKSPACE_ACL", default=False)
        workspace_id, user_id = _resolve_workspace_context(self.headers, payload)
        if enforce_acl:
            if not workspace_id or not user_id:
                return self._send(401, {"error": "Missing workspace context"})
            ok, msg = _check_acl(workspace_id, user_id, str(repo))
            if not ok:
                # If ACL file isn't configured, treat as server misconfig (not user denial)
                if msg == "AGENT_SWARM_ACL_PATH not set":
                    return self._send(500, {"error": msg})
                return self._send(403, {"error": msg})

        cmd = ["python3", "-m", "swarm.cli", "run", "--repo", repo, "--goal", goal]
        env: Dict[str, str] = dict(os.environ)
        if workspace_id:
            # Used by swarm.orchestrator to partition .swarm_work/<workspace_id>/...
            env["AGENT_SWARM_WORKSPACE_SUBDIR"] = workspace_id
        proc = subprocess.Popen(
            cmd,
            cwd=str(SWARM_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        out, err = proc.communicate()

        artifacts_path: Optional[str] = None
        m = re.search(r"^Artifacts:\s+(?P<path>.+)$", out, flags=re.MULTILINE)
        if m:
            artifacts_path = m.group("path").strip()
        return self._send(
            200,
            {
                "ok": proc.returncode == 0,
                "code": proc.returncode,
                "stdout": out,
                "stderr": err,
                "workspaceId": workspace_id,
                "userId": user_id,
                "artifactsPath": artifacts_path,
            },
        )


def main():
    host = "127.0.0.1"
    port = 8787
    server = HTTPServer((host, port), Handler)
    print(f"Agent Swarm Runner listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
