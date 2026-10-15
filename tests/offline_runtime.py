"""A mock HTTP service for exercising the real LangChain/OpenAI integration."""

import base64
from contextlib import ExitStack
import datetime
import json
from pathlib import Path
import socket
import sys
from types import ModuleType
from unittest.mock import Mock, patch

import httpx
import numpy as np
from langchain.chat_models import init_chat_model as real_init
import lesson_support


class OfflineSession:
    def __init__(self):
        self.stack = ExitStack()
        self.requests = []
        self.options = []
        self.client = httpx.Client(transport=httpx.MockTransport(self.respond))
        self.fake_microphone = ModuleType("sounddevice")
        self.fake_microphone.rec = Mock(return_value=np.zeros((120000, 1), dtype="int16"))
        self.fake_microphone.wait = Mock()

    def start(self):
        env = {
            "OPENAI_API_KEY": "sk-offline-test-only", "OPENAI_MODEL": "gpt-5.6-luna",
            "OPENAI_AUDIO_MODEL": "gpt-audio", "OPENAI_REASONING_EFFORT": "none",
        }
        # Point the existence check at a public template, never a user's .env.
        self.stack.enter_context(patch.object(lesson_support, "ENV_PATH", lesson_support.PROJECT_ROOT / ".env.example"))
        self.stack.enter_context(patch.object(lesson_support, "dotenv_values", side_effect=lambda *a, **k: dict(env)))
        self.stack.enter_context(patch.object(lesson_support, "init_chat_model", side_effect=self.initialize))
        self.stack.enter_context(patch.object(socket.socket, "connect", side_effect=AssertionError("Network is forbidden in offline verification")))
        self.stack.enter_context(patch.object(socket.socket, "connect_ex", side_effect=AssertionError("Network is forbidden in offline verification")))
        # Restoring patch.dict(sys.modules) would also remove unrelated lazy imports.
        previous_sounddevice = sys.modules.get("sounddevice")
        sys.modules["sounddevice"] = self.fake_microphone
        def restore_microphone_module():
            if previous_sounddevice is None:
                sys.modules.pop("sounddevice", None)
            else:
                sys.modules["sounddevice"] = previous_sounddevice
        self.stack.callback(restore_microphone_module)
        return self

    def close(self):
        self.stack.close()
        self.client.close()

    def initialize(self, *args, **kwargs):
        self.options.append(kwargs)
        assert kwargs["api_key"].get_secret_value() == "sk-offline-test-only"
        return real_init(*args, **kwargs, http_client=self.client)

    def respond(self, request):
        body = json.loads(request.content)
        self.requests.append((request.url.path, body))
        if request.url.path.endswith("/responses"):
            assert body["tools"] == [{"type": "web_search"}]
            assert body["store"] is False
            return httpx.Response(200, json={
                "id": "resp_offline", "object": "response", "created_at": 0,
                "status": "completed", "model": body["model"],
                "output": [
                    {"id": "ws_offline", "type": "web_search_call", "status": "completed",
                     "action": {"type": "search", "query": "offline fixture"}},
                    {"id": "msg_offline", "type": "message", "role": "assistant", "status": "completed",
                     "content": [{"type": "output_text", "text": "Offline search answer.", "annotations": []}]},
                ],
                "parallel_tool_calls": True, "tools": body["tools"], "tool_choice": "auto",
                "error": None, "incomplete_details": None,
                "usage": {"input_tokens": 10, "output_tokens": 10, "total_tokens": 20,
                          "input_tokens_details": {"cached_tokens": 0},
                          "output_tokens_details": {"reasoning_tokens": 0}},
            })
        if body.get("stream"):
            chunks = [
                {"id": "chatcmpl-stream", "object": "chat.completion.chunk", "created": 0,
                 "model": body["model"], "choices": [{"index": 0, "delta": {
                     "role": "assistant", "content": "Offline streamed answer."}, "finish_reason": None}]},
                {"id": "chatcmpl-stream", "object": "chat.completion.chunk", "created": 0,
                 "model": body["model"], "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
            ]
            content = "".join("data: " + json.dumps(c) + "\n\n" for c in chunks) + "data: [DONE]\n\n"
            return httpx.Response(200, content=content.encode(), headers={"content-type": "text/event-stream"})

        message = {"role": "assistant", "content": "Offline text answer."}
        finish = "stop"
        tools = [tool["function"] for tool in body.get("tools", []) if tool.get("type") == "function"]
        if tools and body["messages"][-1]["role"] != "tool":
            calls = []
            for tool in tools:
                args = {} if tool["name"] == "small_db" else {"x": 28.7296}
                calls.append({"id": "call_" + tool["name"], "type": "function",
                              "function": {"name": tool["name"], "arguments": json.dumps(args)}})
            message.update(content=None, tool_calls=calls)
            finish = "tool_calls"
        elif "response_format" in body:
            message["content"] = json.dumps({"name": "Luna City", "location": "Moon", "vibe": "quiet futuristic", "economy": "research"})
        else:
            messages_text = json.dumps(body["messages"])
            last = str(body["messages"][-1].get("content", ""))
            if "favourite colour" in last.lower():
                message["content"] = "Your favourite colour is green." if "green" in messages_text else "No colour was shared in this conversation."
        return httpx.Response(200, json={
            "id": "chatcmpl-offline", "object": "chat.completion", "created": 0, "model": body["model"],
            "choices": [{"index": 0, "message": message, "finish_reason": finish}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        })

    def inject_image(self, namespace):
        data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1sAAAAASUVORK5CYII=")
        namespace["uploader"].value = ({
            "name": "fixture.png", "type": "image/png", "size": len(data), "content": memoryview(data),
            "last_modified": datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        },)

    def verify(self, name, namespace, start=0, *, multimodal=False):
        requests = self.requests[start:]
        expected = {
            "1.1_foundational_models_openai.ipynb": 5, "1.1_prompting.ipynb": 5,
            "1.2_tools.ipynb": 2, "1.2_web_search.ipynb": 2, "1.3_memory.ipynb": 4,
            "1.4_multimodal_messages.ipynb": 3 if multimodal else 1,
            "1.5_personal_chef.ipynb": 1,
        }
        assert len(requests) == expected[name], (name, len(requests))
        if "foundational_models" in name:
            assert requests[-1][1]["stream"] is True
        elif name == "1.1_prompting.ipynb":
            assert namespace["response"]["structured_response"].name == "Luna City"
        elif name == "1.2_tools.ipynb":
            messages = namespace["response"]["messages"]
            tool_messages = [m for m in messages if m.type == "tool"]
            assert {m.name for m in tool_messages} == {"small_db", "square_root"}
            assert next(m.content for m in tool_messages if m.name == "square_root") == "5.36"
            assert len(messages[1].tool_calls) == 2
        elif name == "1.2_web_search.ipynb":
            assert requests[-1][0].endswith("/responses")
            assert namespace["last_message"].usage_metadata["total_tokens"] == 20
        elif name == "1.3_memory.ipynb":
            assert [len(body["messages"]) for _, body in requests] == [1, 1, 1, 3]
            assert "green" in namespace["response"]["messages"][-1].text
            assert not namespace["agent"].get_state({"configurable": {"thread_id": "new-thread"}}).values
        elif name == "1.4_multimodal_messages.ipynb":
            if multimodal:
                assert requests[1][1]["messages"][-1]["content"][1]["type"] == "image_url"
                audio = requests[2][1]
                assert audio["model"] == "gpt-audio" and "reasoning_effort" not in audio
                assert audio["messages"][-1]["content"][1]["type"] == "input_audio"
                self.fake_microphone.rec.assert_called_once()
            else:
                self.fake_microphone.rec.assert_not_called()
        assert all(option["max_retries"] == 0 for option in self.options)
