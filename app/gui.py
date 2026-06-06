"""
Tax God — Local GUI Launcher
Opens the FastAPI app in a native OS window via pywebview.
"""
import os
import socket
import threading
import time

import uvicorn
import webview


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _run_server(port: int) -> None:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, log_level="warning")


def main() -> None:
    os.environ.setdefault("TAXGOD_LOCAL_MODE", "1")
    os.environ.setdefault("ENVIRONMENT", "development")

    # Load user .env from ~/.tax-god/
    env_path = os.path.expanduser("~/.tax-god/.env")
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)

    port = _find_free_port()
    server_thread = threading.Thread(target=_run_server, args=(port,), daemon=True)
    server_thread.start()

    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.1)

    webview.create_window("Tax God", f"http://127.0.0.1:{port}", width=1400, height=900)
    webview.start()


if __name__ == "__main__":
    main()
