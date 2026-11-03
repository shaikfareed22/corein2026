"""The AWS + Gemini deploy kit (deploy/aws-gemini): its menu goes through the relay's own
parser and its settings template says what the spec says, so a broken kit fails here
before it reaches a box."""

from __future__ import annotations

import json
import pathlib

from nanomuse_cloud.config import LANES, _models_from_env, menu_warnings

KIT = pathlib.Path(__file__).resolve().parents[1] / "deploy" / "aws-gemini"


def _kv(text: str) -> dict[str, str]:
    return dict(line.split("=", 1) for line in text.splitlines() if line and not line.startswith("#") and "=" in line)


def test_menu_is_gemini_chat_only_with_one_pick_per_lane(monkeypatch):
    raw = (KIT / "models.json").read_text(encoding="utf-8")
    assert "\n" not in raw.strip(), "models.json is inlined into .env as one line"
    json.loads(raw)
    monkeypatch.setenv("CLOUD_MODELS", raw)
    models = _models_from_env()
    assert models
    assert all(m.kind == "chat" for m in models), "no picture or clip model: those routes assume DashScope"
    assert all("image" in m.input_modalities for m in models), "the hands send screenshots"
    assert all(m.id.startswith("gemini-") for m in models)
    assert menu_warnings(models) == []
    for lane in LANES:
        assert sum(lane in m.recommended_lanes for m in models) == 1
        assert all(lane in m.lanes for m in models), "every model serves both lanes"


def test_env_template_gemini_settings():
    kv = _kv((KIT / "env.template").read_text(encoding="utf-8"))
    assert kv["CHAT_DEFAULTS"] == "{}", "Gemini rejects enable_thinking"
    assert json.loads(kv["CHAT_DROP"]) == {"enable_thinking": True, "reasoning_effort": ["none"]}, (
        "the hands say no-thinking; Gemini answers 400 to it"
    )
    assert kv["CHAT_TOOL_CALL_SIGNATURE"] == "skip_thought_signature_validator"
    assert kv["UPSTREAM_BASE"] == "https://generativelanguage.googleapis.com/v1beta/openai"
    assert kv["CLOUD_CATALOG"] == "0"
    assert kv["CODE_SENDER"] == "smtp"
    assert kv["SIGNUP_OPEN"] == "1"
    assert kv["CLOUD_MODELS"] == "${CLOUD_MODELS}"
    for name in ("DOMAIN", "CLOUD_SECRET", "CLOUD_ADMIN_TOKEN", "UPSTREAM_KEY", "OPERATOR_EMAIL", "SMTP_PASSWORD"):
        assert "${" + name + "}" in "\n".join(kv.values()), name
