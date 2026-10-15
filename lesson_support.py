"""Shared, portable OpenAI configuration. Importing this module never calls an API."""

import os
from pathlib import Path

from dotenv import dotenv_values
from langchain.chat_models import init_chat_model
from pydantic import SecretStr

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"


def make_model(name=None, *, audio=False, **overrides):
    """Create a model from this repository's .env, without sending a request.

    Use make_model("another-api-model-id") to change the model while keeping
    the same credentials. Keyword overrides take precedence over defaults.
    """
    if not ENV_PATH.is_file():
        raise RuntimeError("Missing .env. Copy .env.example to .env in the course root.")
    settings = dotenv_values(ENV_PATH, interpolate=False)
    key_text = (settings.get("OPENAI_API_KEY") or "").strip()
    if not key_text.startswith("sk-") or "your" in key_text.lower():
        raise RuntimeError("Fill in OPENAI_API_KEY in this repository's .env, then rerun setup.")
    api_key = SecretStr(key_text)
    del key_text
    field = "OPENAI_AUDIO_MODEL" if audio else "OPENAI_MODEL"
    default = "gpt-audio" if audio else "gpt-5.6-luna"
    model_name = name or (settings.get(field) or default).strip()
    effort = (settings.get("OPENAI_REASONING_EFFORT") or "").strip()
    settings.clear()

    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    options = dict(
        model=model_name, model_provider="openai", api_key=api_key,
        base_url="https://api.openai.com/v1", use_responses_api=False,
        max_tokens=1024, timeout=30, max_retries=0,
    )
    if audio:
        options["model_kwargs"] = {"modalities": ["text"]}
    elif effort:
        options["reasoning_effort"] = effort
    options.update(overrides)
    if options["use_responses_api"]:
        options.setdefault("store", False)
    return init_chat_model(**options)
