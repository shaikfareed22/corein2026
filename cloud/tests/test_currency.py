"""CURRENCY / CURRENCY_SYMBOL: the ledger's currency is named once on the relay, every payload
that carries money says it, and the relay's own words use the sign."""

from __future__ import annotations

import httpx
from test_chat_retry import busy_upstream

from nanomuse_cloud.api import create_app
from nanomuse_cloud.config import ModelSpec, Settings
from nanomuse_cloud.db import Database
from nanomuse_cloud.senders import LogSender
from nanomuse_cloud.service import Cloud


def test_symbol_from_code_or_setting(monkeypatch):
    assert Settings().currency == "CNY" and Settings().symbol == "¥"
    monkeypatch.setenv("CURRENCY", "inr")
    assert Settings().currency == "INR" and Settings().symbol == "₹"
    monkeypatch.setenv("CURRENCY", "CHF")
    assert Settings().symbol == "CHF "
    monkeypatch.setenv("CURRENCY_SYMBOL", "Fr.")
    assert Settings().symbol == "Fr."


async def rupee_stack():
    settings = Settings(
        database=":memory:",
        secret="test-secret",
        admin_token="admin",
        upstream_base="http://upstream/v1",
        upstream_key="k",
        public_base="http://cloud.test",
        models=(ModelSpec(id="lite", name="Lite", upstream="lite-up", price_in=8.4, price_out=33.6),),
        currency="INR",
        allowance_cny=0.00001,  # a pool one request empties
        invite_bonus_cny=50,
        usd_cny=84,
    )
    sender = LogSender()
    cloud = Cloud(settings, Database(":memory:"), sender)
    app = create_app(settings, cloud, upstream_transport=httpx.ASGITransport(app=busy_upstream([])))
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://cloud.test")
    return client, sender


async def sign_in(client, sender):
    r = await client.post("/v1/auth/code", json={"identifier": "a@example.com"})
    assert r.status_code == 204, r.text
    _, code = sender.sent[-1]
    r = await client.post("/v1/auth/verify", json={"identifier": "a@example.com", "code": code, "device": "pixel"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['api_key']}"}


async def test_every_money_payload_names_the_currency():
    client, sender = await rupee_stack()
    cfg = (await client.get("/v1/config")).json()
    assert (cfg["currency"], cfg["currency_symbol"], cfg["allowance_cny"]) == ("INR", "₹", 0.00001)
    headers = await sign_in(client, sender)
    me = (await client.get("/v1/me", headers=headers)).json()
    assert me["spend"]["currency"] == "INR" and me["spend"]["currency_symbol"] == "₹"
    assert me["spend"]["usd_cny"] == 84
    admin = (await client.get("/v1/admin/overview", headers={"X-Admin-Token": "admin"})).json()["settings"]
    assert admin["currency"] == "INR" and admin["currency_symbol"] == "₹"


async def test_the_refusal_speaks_in_the_relays_currency():
    client, sender = await rupee_stack()
    headers = await sign_in(client, sender)
    ask = {"model": "lite", "messages": [{"role": "user", "content": "hi"}]}
    assert (await client.post("/v1/chat/completions", headers=headers, json=ask)).status_code == 200  # the first turn empties the pool
    r = await client.post("/v1/chat/completions", headers=headers, json=ask)
    assert r.status_code == 429, r.text
    err = r.json()["error"]
    assert err["code"] == "allowance_exhausted"
    assert err["currency_symbol"] == "₹" and err["currency"] == "INR"
    assert "₹" in err["message"] and "¥" not in err["message"]
    assert "+₹50 for each of you" in err["message"]
