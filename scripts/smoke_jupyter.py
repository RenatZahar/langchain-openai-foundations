"""Start JupyterLab on localhost, check course files/kernel, then shut it down."""

import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    token = secrets.token_urlsafe(32)
    env = dict(os.environ)
    for name in ("OPENAI_API_KEY", "LANGSMITH_API_KEY"):
        env.pop(name, None)
    env["JUPYTER_TOKEN"] = token
    runtime = ROOT / "runtime/jupyter-smoke"
    runtime.mkdir(parents=True, exist_ok=True)
    env["JUPYTER_RUNTIME_DIR"] = str(runtime)
    base = f"http://127.0.0.1:{port}"

    def fetch(path, method="GET"):
        request = urllib.request.Request(base + path, method=method,
                                         headers={"Authorization": "token " + token})
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status, response.read()

    process = subprocess.Popen(
        [sys.executable, "-m", "jupyter", "lab", "--no-browser",
         "--ServerApp.ip=127.0.0.1", f"--ServerApp.port={port}", "--ServerApp.port_retries=0",
         f"--ServerApp.root_dir={ROOT}"],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    try:
        deadline = time.monotonic() + 45
        while True:
            try:
                status, raw = fetch("/api/kernelspecs")
                break
            except (urllib.error.URLError, TimeoutError, OSError):
                if process.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("JupyterLab did not become ready; run the README launch command to inspect its diagnostics.") from None
                time.sleep(0.25)
        assert status == 200
        assert "langchain-openai-foundations" in json.loads(raw)["kernelspecs"]
        status, raw = fetch("/api/contents/notebooks")
        assert status == 200
        assert len([item for item in json.loads(raw)["content"] if item["name"].endswith(".ipynb")]) == 7
        status, raw = fetch("/lab")
        assert status == 200 and b"<!doctype html>" in raw.lower()
        print("PASS: authenticated JupyterLab startup, course kernel, seven notebooks and /lab HTTP response.")
    finally:
        try:
            fetch("/api/shutdown", "POST")
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            else:
                process.kill()
            process.wait(timeout=5)
    print("PASS: temporary JupyterLab server stopped; no OpenAI request was made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
