"""Execute notebook sources offline; --kernels also checks real Jupyter execution."""

import argparse
import ast
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import runpy
import sys
from unittest.mock import patch

import nbformat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
from tests.offline_runtime import OfflineSession
import lesson_support


def run_sources(relative, *, multimodal=False):
    path = ROOT / relative
    original_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    namespace = {}
    session = OfflineSession().start()
    previous_cwd = Path.cwd()
    try:
        # Also exercises portable setup when the kernel starts inside notebooks/.
        os.chdir(path.parent)
        with contextlib.redirect_stdout(io.StringIO()):
            for index, cell in enumerate(notebook.cells):
                assert not re.search(r"[\u0400-\u04ff]", cell.source), (relative, index)
                if cell.cell_type != "code":
                    # Python reference blocks are documentation, but must still parse.
                    for code in re.findall(r"```python\n(.*?)```", cell.source, re.S):
                        ast.parse(code)
                    continue
                assert cell.outputs == [] and cell.execution_count is None
                source = cell.source
                if multimodal:
                    source = source.replace("audio_enabled = False", "audio_enabled = True")
                ast.parse(source)
                exec(compile(source, f"{relative}:cell{index}", "exec"), namespace)
                if multimodal and "uploader = FileUpload" in source:
                    session.inject_image(namespace)
            session.verify(path.name, namespace, multimodal=multimodal)
        count = len(session.requests)
    finally:
        os.chdir(previous_cwd)
        session.close()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == original_hash
    return count


def check_configuration_and_script():
    session = OfflineSession().start()
    try:
        with patch.object(lesson_support, "dotenv_values", return_value={}):
            try:
                lesson_support.make_model()
            except RuntimeError as error:
                assert "OPENAI_API_KEY" in str(error)
            else:
                raise AssertionError("Empty keys must fail before calling the API")
        assert not session.requests
        assert lesson_support.make_model("gpt-5.6-sol").model_name == "gpt-5.6-sol"
        assert not session.requests
        with contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(ROOT / "personal_chef.py"), run_name="offline_import")
            assert not session.requests
            runpy.run_path(str(ROOT / "personal_chef.py"), run_name="__main__")
            assert len(session.requests) == 1
    finally:
        session.close()


def run_kernel(relative, kernel_name):
    from nbclient import NotebookClient

    original = ROOT / relative
    notebook = nbformat.read(original, as_version=4)
    bootstrap = (
        f"import sys\nsys.path.insert(0, {str(ROOT)!r})\n"
        "from tests.offline_runtime import OfflineSession\n"
        "_offline_session = OfflineSession().start()\n"
    )
    check = (
        f"_offline_session.verify({original.name!r}, globals())\n"
        "_offline_session.close()\n"
    )
    notebook.cells.insert(0, nbformat.v4.new_code_cell(bootstrap))
    notebook.cells.append(nbformat.v4.new_code_cell(check))
    client = NotebookClient(
        notebook, timeout=120, kernel_name=kernel_name,
        resources={"metadata": {"path": str(original.parent)}},
    )
    client.execute()
    assert not any(output.output_type == "error" for cell in notebook.cells
                   if cell.cell_type == "code" for output in cell.outputs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernels", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "course.json").read_text(encoding="utf-8"))
    total = 0
    for relative in manifest["notebooks"]:
        count = run_sources(relative)
        total += count
        print(f"PASS: {relative} ({count} mock HTTP requests)", flush=True)
    total += run_sources("notebooks/1.4_multimodal_messages.ipynb", multimodal=True)
    print("PASS: optional image/audio branches with synthetic fixtures", flush=True)
    check_configuration_and_script()
    print("PASS: empty-key guard, named model override and script import/main", flush=True)
    if args.kernels:
        for relative in manifest["notebooks"]:
            run_kernel(relative, manifest["kernel"])
            print(f"PASS: fresh Jupyter kernel: {relative}", flush=True)
    print(f"PASS: {total + 1} mock HTTP requests in source checks; no real API, keys or microphone used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
