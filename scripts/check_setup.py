"""Check local readiness without calling OpenAI or displaying credentials."""

import argparse
import ast
import importlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-empty-key", action="store_true", help="Validate the distributed template before adding a key.")
    args = parser.parse_args()
    errors = []
    if not ((3, 12) <= sys.version_info[:2] < (3, 14)):
        errors.append("Use Python 3.12 or 3.13; Python 3.12 is the tested quick-start version.")
    if sys.prefix == sys.base_prefix:
        errors.append("Use the course virtual environment, not the global Python.")
    for name in ["dotenv", "langchain", "langchain_openai", "langgraph", "openai", "pydantic", "jupyterlab", "ipykernel", "nbformat", "nbclient", "ipywidgets", "httpx", "scipy", "numpy"]:
        try:
            importlib.import_module(name)
        except ImportError:
            errors.append(f"Missing import: {name}. Install requirements.txt with this Python.")
    if errors:
        for error in errors:
            print("ERROR:", error)
        return 1

    from dotenv import dotenv_values
    from jupyter_client.kernelspec import KernelSpecManager
    import nbformat

    manifest = json.loads((ROOT / "course.json").read_text(encoding="utf-8"))
    env_path = ROOT / ".env"
    if not env_path.is_file():
        errors.append("Missing .env. Copy .env.example to .env first.")
    else:
        settings = dotenv_values(env_path, interpolate=False)
        key = (settings.get("OPENAI_API_KEY") or "").strip()
        ready = key.startswith("sk-") and "your" not in key.lower()
        settings.clear()
        del key
        if ready:
            print("PASS: OPENAI_API_KEY is present (not displayed; API access not tested).")
        elif args.allow_empty_key:
            print("TEMPLATE: OPENAI_API_KEY is empty; add your key before running API cells.")
        else:
            errors.append("Fill in OPENAI_API_KEY in .env. The key was not displayed.")

    for relative in manifest["notebooks"]:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"Missing notebook: {relative}")
            continue
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        for cell in notebook.cells:
            if cell.cell_type == "code":
                compile(cell.source, relative, "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
            if re.search(r"[\u0400-\u04ff]", cell.source):
                errors.append(f"Non-English source found in {relative}")
    specs = KernelSpecManager().get_all_specs()
    kernel = manifest["kernel"]
    if kernel not in specs:
        errors.append("Register the kernel using the ipykernel install command in README.md.")
    else:
        executable = Path(specs[kernel]["spec"]["argv"][0]).resolve()
        if executable != Path(sys.executable).resolve():
            errors.append("The course kernel points to a different Python. Rerun kernel registration in this environment.")
        else:
            print("PASS: course kernel points to the current virtual environment.")
    for error in errors:
        print("ERROR:", error)
    if errors:
        return 1
    print(f"PASS: {len(manifest['notebooks'])} notebooks, imports and local configuration checked.")
    print("No OpenAI request was made. Live access, billing and microphone hardware are not verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
