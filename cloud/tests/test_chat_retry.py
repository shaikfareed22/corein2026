"""CHAT_RETRIES / CHAT_FALLBACK: a busy provider (429, 5xx) is asked again before the app
hears about it, and the last try can go to another model."""

from __future__ import annotations

import json

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from nanomuse_cloud.api import chat_retry_pause, create_app
from nanomuse_cloud.config import ModelSpec, Settings
from nanomuse_cloud.db import Database
from nanomuse_cloud.senders import LogSender
from nanomuse_cloud.service import Cloud

BUSY = [{"error": {"code": 503, "message": "This model is currently experiencing high demand.", "status": "UNAVAILABLE"}}]


def busy_upstream(statuses: list[int]) -> FastAPI:
    """Answers the queued statuses one per request, then 200."""
    up = FastAPI()
    up.state.models = []
    queue = list(statuses)

    @up.post("/v1/chat/completions")
    async def chat(request: Request):
        body = await request.json()
        up.state.models.append(body["model"])
        status = queue.pop(0) if queue else 200
        if status != 200:
            return JSONResponse(status_code=status, content=BUSY)
        if not body.get("stream"):
            return {
                "choices": [{"message": {"role": "assistant", "content": "hello"}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
            }

        async def gen():
            yield b'data: {"choices":[{"delta":{"content":"hello"}}]}\n\n'
            yield b'data: {"choices":[],"usage":{"prompt_tokens":3,"completion_tokens":1,"total_tokens":4}}\n\n'
            yield b"data: [DONE]\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    return up


async def stack(statuses: list[int], **overrides):
    up = busy_upstream(statuses)
    settings = Settings(
        database=":memory:",
        secret="test-secret",
        admin_token="admin",
        upstream_base="http://upstream/v1",
        upstream_key="k",
        public_base="http://cloud.test",
        models=(ModelSpec(id="lite", name="Lite", upstream="lite-up"),),
        chat_retry_max_s=0,
        **overrides,
    )
    sender = LogSender()
    cloud = Cloud(settings, Database(":memory:"), sender)
    app = create_app(settings, cloud, upstream_transport=httpx.ASGITransport(app=up))
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://cloud.test")
    r = await client.post("/v1/auth/code", json={"identifier": "a@example.com"})
    assert r.status_code == 204, r.text
    _, code = sender.sent[-1]
    r = await client.post("/v1/auth/verify", json={"identifier": "a@example.com", "code": code, "device": "pixel"})
    assert r.status_code == 200, r.text
    return client, up, {"Authorization": f"Bearer {r.json()['api_key']}"}


def ask(stream: bool) -> dict:
    return {"model": "lite", "stream": stream, "messages": [{"role": "user", "content": "hi"}]}


async def test_a_busy_provider_is_asked_again():
    client, up, headers = await stack([503, 429], chat_retries=3)
    r = await client.post("/v1/chat/completions", headers=headers, json=ask(False))
    assert r.status_code == 200, r.text
    assert r.json()["choices"][0]["message"]["content"] == "hello"
    assert up.state.models == ["lite-up"] * 3


async def test_a_busy_provider_is_asked_again_while_streaming():
    client, up, headers = await stack([503, 503], chat_retries=3)
    async with client.stream("POST", "/v1/chat/completions", headers=headers, json=ask(True)) as r:
        assert r.status_code == 200
        body = (await r.aread()).decode()
    data = [ln for ln in body.split("\n") if ln.startswith("data:")]
    assert data[-1] == "data: [DONE]"
    assert not any("error" in json.loads(ln[5:]) for ln in data[:-1])
    assert json.loads(data[0][5:])["choices"][0]["delta"]["content"] == "hello"
    assert body.count(": the provider is busy") == 2, "the app's connection is kept awake while waiting"
    assert len(up.state.models) == 3


async def test_without_the_setting_the_first_answer_stands():
    client, up, headers = await stack([503])
    r = await client.post("/v1/chat/completions", headers=headers, json=ask(False))
    assert r.status_code == 502
    assert len(up.state.models) == 1


async def test_tries_run_out_and_the_app_hears_the_providers_words():
    client, up, headers = await stack([503] * 5, chat_retries=2)
    async with client.stream("POST", "/v1/chat/completions", headers=headers, json=ask(True)) as r:
        body = (await r.aread()).decode()
    data = [ln for ln in body.split("\n") if ln.startswith("data:")]
    assert "high demand" in json.loads(data[0][5:])["error"]["upstream"]
    assert len(up.state.models) == 3
    me = (await client.get("/v1/me", headers=headers)).json()
    assert not [row for row in me["recent"] if row["kind"] == "chat"], "nothing came, nothing is owed"


async def test_a_refusal_is_not_asked_again():
    client, up, headers = await stack([400], chat_retries=3)
    r = await client.post("/v1/chat/completions", headers=headers, json=ask(False))
    assert r.status_code == 400
    assert len(up.state.models) == 1


async def test_the_last_try_goes_to_the_fallback_model():
    client, up, headers = await stack([429, 429], chat_retries=2, chat_fallback="big-up")
    r = await client.post("/v1/chat/completions", headers=headers, json=ask(False))
    assert r.status_code == 200, r.text
    assert up.state.models == ["lite-up", "lite-up", "big-up"]
    assert r.json()["model"] == "lite", "the app sees the model it asked for"


def test_the_pause_is_what_the_provider_asks_for_up_to_the_cap():
    assert chat_retry_pause(0, "7", b"", 20) == 7
    assert chat_retry_pause(0, None, b'{"details": [{"retryDelay": "23.5s"}]}', 60) == 23.5
    assert chat_retry_pause(0, None, b'{"retryDelay": "50s"}', 20) == 20
    assert [chat_retry_pause(n, None, b"", 20) for n in range(5)] == [2, 4, 8, 16, 20]
    assert chat_retry_pause(1, "soon", b"", 20) == 4


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("CHAT_RETRIES", "5")
    monkeypatch.setenv("CHAT_RETRY_MAX_S", "15")
    monkeypatch.setenv("CHAT_FALLBACK", "gemini-3.8-flash")
    s = Settings()
    assert (s.chat_retries, s.chat_retry_max_s, s.chat_fallback) == (5, 15.0, "gemini-3.8-flash")
