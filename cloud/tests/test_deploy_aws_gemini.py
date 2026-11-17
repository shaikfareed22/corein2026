"""The AWS deploy kit (deploy/aws-gemini, M4 Spider behind it since 0.28): its menu goes through the relay's own
parser and its settings template says what the spec says, so a broken kit fails here
before it reaches a box."""

from __future__ import annotations

import json
import pathlib

from nanomuse_cloud.config import LANES, _models_from_env, menu_warnings

KIT = pathlib.Path(__file__).resolve().parents[1] / "deploy" / "aws-gemini"


def _kv(text: str) -> dict[str, str]:
    return dict(line.split("=", 1) for line in text.splitlines() if line and not line.startswith("#") and "=" in line)


SPIDER_MODELS = {"auto", "qwen/qwen3.8-flash", "xiaomi/mimo-v2.6-flash", "meta/muse-spark-1.3-contributor", "meta/muse-ember"}


def test_menu_is_chat_only_with_one_pick_per_lane(monkeypatch):
    raw = (KIT / "models.json").read_text(encoding="utf-8")
    assert "\n" not in raw.strip(), "models.json is inlined into .env as one line"
    json.loads(raw)
    monkeypatch.setenv("CLOUD_MODELS", raw)
    models = _models_from_env()
    assert models
    assert all(m.kind == "chat" for m in models), "no picture or clip model: those routes assume DashScope"
    assert all("image" in m.input_modalities for m in models), "the hands send screenshots"
    assert {m.upstream for m in models} <= SPIDER_MODELS, "upstream names as M4 Spider lists them"
    assert all("/" not in m.id for m in models), "the apps' ids stay plain"
    assert menu_warnings(models) == []
    for lane in LANES:
        assert sum(lane in m.recommended_lanes for m in models) == 1
        assert all(lane in m.lanes for m in models), "every model serves both lanes"


def test_env_template_settings():
    kv = _kv((KIT / "env.template").read_text(encoding="utf-8"))
    assert kv["CHAT_DEFAULTS"] == "{}"
    assert json.loads(kv["CHAT_DROP"]) == {"enable_thinking": True}, (
        "reasoning_effort none stays: M4 Spider honours it and its models think long otherwise"
    )
    assert kv["CHAT_TOOL_CALL_SIGNATURE"] == "", "Google's placeholder has no place at another provider"
    assert kv["CURRENCY"] == "INR" and float(kv["USD_CNY"]) > 50, "the kit prices in rupees"
    assert float(kv["ALLOWANCE_CNY"]) >= 50 and float(kv["INVITE_BONUS_CNY"]) > 0
    menu = json.loads((KIT / "models.json").read_text(encoding="utf-8"))
    rate = float(kv["USD_CNY"])
    for m in menu:  # nominal rupee prices (the provider bills a flat plan): they pace the allowance
        assert 0.05 * rate <= m["price_in"] <= 0.5 * rate, m["id"]
        assert 0.3 * rate <= m["price_out"] <= 3 * rate, m["id"]
    assert int(kv["CHAT_RETRIES"]) >= 3, "a model over its five-hour quota answers 429"
    assert kv["CHAT_FALLBACK"] in {m["upstream"] for m in json.loads((KIT / "models.json").read_text(encoding="utf-8"))}
    assert kv["UPSTREAM_BASE"] == "https://admin.m4spider.com/v1"
    assert kv["CLOUD_CATALOG"] == "0"
    assert kv["CODE_SENDER"] == "smtp"
    assert kv["SIGNUP_OPEN"] == "1"
    assert kv["CLOUD_MODELS"] == "${CLOUD_MODELS}"
    for name in ("DOMAIN", "CLOUD_SECRET", "CLOUD_ADMIN_TOKEN", "UPSTREAM_KEY", "OPERATOR_EMAIL", "SMTP_PASSWORD"):
        assert "${" + name + "}" in "\n".join(kv.values()), name
