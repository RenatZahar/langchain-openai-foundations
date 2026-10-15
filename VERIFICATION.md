# Verification

Verified on 2026-10-15 on Windows with a newly created Python 3.12.2 virtual environment.

| Check | Result |
| --- | --- |
| Fresh `pip install -r requirements.txt` | Passed; 128 installed distributions |
| `python -m pip check` | Passed; no broken requirements |
| Register the course kernel with `ipykernel install --sys-prefix` | Passed |
| `python scripts/check_setup.py --allow-empty-key` | Passed; the distributed key is intentionally empty |
| `python scripts/verify_offline.py --kernels` | Passed; all seven notebooks execute in fresh kernels |
| Mocked source execution and optional media | Passed; 24 mock HTTP requests, including script execution |
| JupyterLab localhost startup | Passed; authenticated `/lab`, notebook listing and kernelspec API |
| Temporary JupyterLab shutdown | Passed; the verifier stops its own server |
| Notebook language, syntax and outputs | English text; valid notebook/Markdown Python examples; outputs cleared |
| Source preservation | Original learning notebooks were not edited |

The fixtures exercise real LangChain agents and OpenAI SDK parsing while replacing
HTTP responses. They cover streaming, structured output, two Python tool calls in
one model reply, thread history/isolation, Responses web search payloads, and
image/audio serialization. The microphone is synthetic, and network connections
are blocked during notebook execution. The tests do not read a real API key.

The text notebook cells make 20 mocked HTTP requests in total. The extra image/audio
run makes three, and the script makes one. Fresh-kernel execution repeats the
default notebook checks in isolated Python processes.

## Scope of the result

These checks establish local startup and code execution with mocked services.
They do not establish live OpenAI credentials, project quota, model availability,
search quality, real costs, microphone hardware or behavior on macOS/Linux.
Fill in your own `.env` and run `scripts/check_setup.py` before trying API cells.
No paid OpenAI request was made during preparation.

`requirements.lock.txt` records the complete clean verification environment.
