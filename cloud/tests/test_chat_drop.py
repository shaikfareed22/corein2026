"""CHAT_DROP: fields a provider refuses, removed before the request goes upstream. Gemini's
OpenAI layer answers 400 to `enable_thinking` (unknown field) and to `reasoning_effort:
"none"` (checked 2026-11-03), and both are how an app says "no thinking" — the phone's hands
run that way on every screenshot step."""

from __future__ import annotations

import json

from nanomuse_cloud.api import apply_chat_drops, relay_error_body, upstream_detail
from nanomuse_cloud.config import Settings

GEMINI = {"enable_thinking": True, "reasoning_effort": ["none"]}


def test_drops_what_gemini_refuses_and_keeps_the_rest():
    body = {"model": "m", "enable_thinking": False, "reasoning_effort": "none", "temperature": 0}
    apply_chat_drops(body, GEMINI)
    assert body == {"model": "m", "temperature": 0}


def test_a_real_effort_level_stays():
    body = {"reasoning_effort": "low", "enable_thinking": True}
    apply_chat_drops(body, GEMINI)
    assert body == {"reasoning_effort": "low"}
    body = {"reasoning_effort": "NONE "}
    apply_chat_drops(body, GEMINI)
    assert body == {}


def test_empty_rule_changes_nothing():
    body = {"enable_thinking": False, "reasoning_effort": "none"}
    apply_chat_drops(body, {})
    assert body == {"enable_thinking": False, "reasoning_effort": "none"}


def test_setting_from_env(monkeypatch):
    monkeypatch.setenv("CHAT_DROP", json.dumps(GEMINI))
    assert Settings().chat_drop == GEMINI
    monkeypatch.delenv("CHAT_DROP")
    assert Settings().chat_drop == {}


GEMINI_400 = (
    b'[{"error": {"code": 400, "message": "Unknown name \\"enable_thinking\\": Cannot find field.", "status": "INVALID_ARGUMENT"}}]'
)


def test_gemini_list_shaped_error_is_read():
    assert upstream_detail("chat", 400, "gemini-3.5-flash-lite", GEMINI_400).endswith('Unknown name "enable_thinking": Cannot find field.')
    err = relay_error_body(400, GEMINI_400)["error"]
    assert err["code"] == "upstream_400"
    assert "enable_thinking" in err["message"]
