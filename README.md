# LangChain OpenAI Foundations

An English, OpenAI-only adaptation of the seven Module 1 notebooks from
[LangChain Academy: Introduction to LangChain](https://academy.langchain.com/courses/foundation-introduction-to-langchain-python).
It follows the learning path we used: inspect model responses, add tools, understand
agent calls, add conversation memory, and combine everything in a recipe assistant.
LangChain agents use LangGraph underneath; this is not the separate LangGraph course.

## Quick start on Windows (PowerShell)

Install **Python 3.12** first. Git is optional if you download the repository as a ZIP.
Copy/extract the whole repository into any folder, then open a terminal in that folder.
If this repository has been published, you can also clone its URL:

```powershell
git clone <repository-url> langchain-openai-foundations
cd langchain-openai-foundations
```

### 1. Create and fill in `.env`

Git clones contain `.env.example`; the local handoff/ZIP also includes a blank `.env`.
Create `.env` if it is missing, then open it:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Fill in **your own OpenAI API key** after `OPENAI_API_KEY=`. Leave the other defaults
for the first run. The helper reads only this repository's `.env`, never a parent
project's file or another user's key. `.env` is excluded from Git.

### 2. Create an environment and install all lesson dependencies

Run from the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

These commands use the environment directly, so PowerShell activation-policy
changes are unnecessary. Python 3.13 is also permitted, but the verified setup uses 3.12.

### 3. Register the notebook kernel and check setup

```powershell
.\.venv\Scripts\python.exe -m ipykernel install --sys-prefix --name langchain-openai-foundations --display-name "Python (LangChain OpenAI)"
.\.venv\Scripts\python.exe scripts/check_setup.py
```

The check validates imports, notebook files and syntax, the selected Python kernel,
and key presence. It never calls OpenAI and never prints the key. To check the
distributed project before adding a key, use `scripts/check_setup.py --allow-empty-key`.

### 4. Open the lessons

```powershell
.\.venv\Scripts\python.exe -m jupyter lab
```

Open `notebooks/1.1_foundational_models_openai.ipynb`, select
**Python (LangChain OpenAI)**, and execute cells from top to bottom.
In VS Code you can instead open a notebook and choose this repository's
`.venv/Scripts/python.exe` as its kernel. Restart the kernel when switching projects.

## macOS / Linux

Use the same folder and `.env.example`, then:

```bash
test -f .env || cp .env.example .env
# Edit .env and add your own OPENAI_API_KEY before running API cells.
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m ipykernel install --sys-prefix --name langchain-openai-foundations --display-name "Python (LangChain OpenAI)"
.venv/bin/python scripts/check_setup.py
.venv/bin/python -m jupyter lab
```

## Lesson order

| Notebook | What you learn |
| --- | --- |
| [1.1 Models](notebooks/1.1_foundational_models_openai.ipynb) | Model objects, AIMessage, metadata, agents, explicit history and streaming |
| [1.1 Prompting](notebooks/1.1_prompting.ipynb) | System prompts, few-shot examples, text formatting and Pydantic structured output |
| [1.2 Tools](notebooks/1.2_tools.ipynb) | Python `@tool`, a small mock database, two tool calls and their results |
| [1.2 Web search](notebooks/1.2_web_search.ipynb) | Built-in OpenAI search through Responses API and normalized usage metadata |
| [1.3 Memory](notebooks/1.3_memory.ipynb) | Calls without memory, `InMemorySaver`, `thread_id` and a summarization reference |
| [1.4 Multimodal](notebooks/1.4_multimodal_messages.ipynb) | Text, a user-uploaded PNG/JPEG and explicitly enabled microphone input |
| [1.5 Personal chef](notebooks/1.5_personal_chef.ipynb) | One agent combining instructions, web search and conversation memory |

`personal_chef.py` is an optional script version. Running it sends a sample question
and may use paid web search; importing it does not send requests.
This repository covers Module 1 only. The upstream course continues with MCP,
runtime context, state, multi-agent systems and production middleware.

## Configuration and costs

```dotenv
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.6-luna
OPENAI_AUDIO_MODEL=gpt-audio
OPENAI_REASONING_EFFORT=none
```

The default helper uses the OpenAI endpoint, a 1024-token output limit, a 30-second
HTTP timeout and no HTTP retries. LangSmith tracing is disabled. Built-in web search
uses Responses API with `store=False`; ordinary text examples use Chat Completions.
Calls made with your key are billed by OpenAI. Web search has an additional tool fee.
An agent invocation may make several model calls. Summary generation, if you add
the reference middleware, also makes additional calls.

To choose a different text model, change `OPENAI_MODEL` or call
`make_model("another-api-model-id")`. Model capabilities and parameters differ:
clear `OPENAI_REASONING_EFFORT` if a model does not support this setting. The helper
rereads `.env` when it creates a model; recreate the agent or restart the kernel
after changing settings. No API request occurs while creating a model object.

## Optional image and audio sections

Without an uploaded image, the image request is skipped. Audio is disabled by
default. To record five seconds, set `audio_enabled = True`; the following cell
sends that recording to OpenAI. Use a sample recording you are comfortable sharing.
`OPENAI_AUDIO_MODEL` must accept audio input; it is separate from the text model.
The default retains the original lesson's `gpt-audio`; availability can change.

Microphone recording requires a working input device and PortAudio. Windows wheels
normally include the library; Linux may require a system package such as
`libportaudio2` (Debian/Ubuntu). Text, tools, search and memory do not require a microphone.
The offline checks replace the microphone with synthetic data.

## Offline verification

From the repository root, with the dependencies installed:

```powershell
.\.venv\Scripts\python.exe scripts/verify_offline.py
```

The verifier runs notebook code with fake credentials and mocked OpenAI HTTP
responses, blocks network connections and does not overwrite notebook outputs.
It covers tool execution, streaming, structured output, memory isolation and
optional image/audio serialization. A missing real key does not prevent this test.
Use `--kernels` to additionally execute all seven notebooks in fresh Jupyter kernels.

`requirements.txt` pins direct lesson dependencies. `requirements.lock.txt` records
the full environment used for the clean-install check; it is a Windows/Python 3.12
snapshot, while the direct requirements are the normal cross-platform entry point.
See [VERIFICATION.md](VERIFICATION.md) for the checks performed and their limits.

## Troubleshooting

- **`No module named langchain`:** the notebook is using another Python. Select
  this repository's environment and rerun kernel registration.
- **Missing/empty API key:** create `.env` from `.env.example` in this repository,
  fill the key and rerun setup. Do not paste keys into notebook cells or outputs.
- **401 / quota / model access errors:** local readiness does not establish API
  account permissions or credit. Check the key's project and model access.
- **Old variables after editing:** restart the kernel and run cells in order.
- **A new thread does not know an old thread:** `InMemorySaver` is thread-scoped.
  Cross-conversation user facts require a separate profile/store.

## Sources and attribution

Original teaching material: [langchain-ai/lca-lc-foundations](https://github.com/langchain-ai/lca-lc-foundations),
licensed under MIT. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
This is an independent adaptation, not an official LangChain course release.

Official API references: [GPT-5.6 Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna),
[web search](https://developers.openai.com/api/docs/guides/tools-web-search),
[structured output](https://developers.openai.com/api/docs/guides/structured-outputs),
[audio model](https://developers.openai.com/api/docs/models/gpt-audio).
