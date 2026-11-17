"""Relay 0.28: the model provider — UPSTREAM_BASE and UPSTREAM_KEY — set from the operator's
page while the relay runs: in force on the next request, kept across restarts, tested before
it is saved, and never echoed back in full."""

from __future__ import annotations

from test_accounts import auth, make
from test_cloud import sign_up

ADMIN = {"X-Admin-Token": "admin"}


def ask(model: str = "qwen3.8-flash") -> dict:
    return {"model": model, "messages": [{"role": "user", "content": "hi"}]}


async def test_the_key_is_shown_by_its_ends_and_changes_on_the_next_request():
    app, client, sender, up, cloud, settings = make(upstream_key="sk-upstream-key-from-the-env-0001")
    rt = (await client.get("/v1/admin/settings", headers=ADMIN)).json()
    assert rt["values"]["upstream_key"] == "sk-ups…0001" and rt["env"]["upstream_key"] == "sk-ups…0001"
    assert rt["values"]["upstream_base"] == "http://upstream/compat/v1"
    assert "sk-upstream-key-from-the-env-0001" not in str(rt)

    acct = await sign_up(client, sender, "13800138000", "pixel")
    r = await client.post("/v1/chat/completions", headers=auth(acct["api_key"]), json=ask())
    assert r.status_code == 200, r.text
    assert up.state.requests[-1][1]["authorization"] == "Bearer sk-upstream-key-from-the-env-0001"

    r = await client.post("/v1/admin/settings", headers=ADMIN, json={"upstream_key": " sk-rotated-key-0000000000002 "})
    assert r.status_code == 200, r.text
    assert r.json()["values"]["upstream_key"] == "sk-rot…0002" and r.json()["overridden"]["upstream_key"]
    r = await client.post("/v1/chat/completions", headers=auth(acct["api_key"]), json=ask())
    assert r.status_code == 200, r.text
    assert up.state.requests[-1][1]["authorization"] == "Bearer sk-rotated-key-0000000000002"
    # the audit line says a key changed, never which
    assert all("sk-rotated-key" not in str(dict(row)) for row in cloud.db.audit_recent(20))
    # the environment's key is back on request
    r = await client.post("/v1/admin/settings", headers=ADMIN, json={"upstream_key": None})
    assert r.status_code == 200 and not r.json()["overridden"]["upstream_key"]
    await client.post("/v1/chat/completions", headers=auth(acct["api_key"]), json=ask())
    assert up.state.requests[-1][1]["authorization"] == "Bearer sk-upstream-key-from-the-env-0001"


async def test_the_address_is_checked_and_the_catalog_forgets_the_old_provider():
    app, client, sender, up, cloud, settings = make()
    for bad in ("ftp://x.example.com/v1", "http://api.example.com/v1", "https://", "https://a.example.com/v1?x=1", "not a url"):
        r = await client.post("/v1/admin/settings", headers=ADMIN, json={"upstream_base": bad})
        assert r.status_code == 400, (bad, r.text)
    r = await client.post("/v1/admin/settings", headers=ADMIN, json={"upstream_key": "short"})
    assert r.status_code == 400 and "upstream_key" in r.text
    r = await client.post("/v1/admin/settings", headers=ADMIN, json={"upstream_key": "has a space inside it"})
    assert r.status_code == 400

    seen = []
    cloud.on_upstream_change = lambda: seen.append(True)
    r = await client.post("/v1/admin/settings", headers=ADMIN, json={"upstream_base": "https://api.example.com/v1/"})
    assert r.status_code == 200 and r.json()["values"]["upstream_base"] == "https://api.example.com/v1"
    assert seen == [True]
    # a change of allowance does not touch the catalog
    await client.post("/v1/admin/settings", headers=ADMIN, json={"allowance_cny": 3})
    assert seen == [True]
    # a name without dots may be plain http (a box on the LAN, this test's fake)
    r = await client.post("/v1/admin/settings", headers=ADMIN, json={"upstream_base": "http://upstream/compat/v1"})
    assert r.status_code == 200, r.text
    acct = await sign_up(client, sender, "13800138000", "pixel")
    r = await client.post("/v1/chat/completions", headers=auth(acct["api_key"]), json=ask())
    assert r.status_code == 200, r.text


async def test_the_page_tests_a_provider_before_saving_it():
    app, client, sender, up, cloud, settings = make()
    r = await client.post("/v1/admin/settings/upstream-test", headers=ADMIN, json={})
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["ok"] and out["status"] == 200 and out["models"] == len(up.state.catalog_ids)
    assert "qwen3.8-flash" in out["missing"], "the fake's list lacks the menu's default; the page says so"
    assert up.state.requests[-1][1]["authorization"] == "Bearer sk-upstream"
    # with a key and an address typed but not saved: those are used, nothing is stored
    r = await client.post("/v1/admin/settings/upstream-test", headers=ADMIN, json={"key": "sk-typed-not-saved-000001", "base": "http://upstream/compat/v1/"})
    assert r.json()["ok"] and up.state.requests[-1][1]["authorization"] == "Bearer sk-typed-not-saved-000001"
    assert cloud.db.settings_all() == {}
    # a wrong address is reported, not raised
    r = await client.post("/v1/admin/settings/upstream-test", headers=ADMIN, json={"base": "http://upstream/nowhere/v1"})
    assert r.status_code == 200 and not r.json()["ok"] and r.json()["status"] == 404
    r = await client.post("/v1/admin/settings/upstream-test", headers={"X-Admin-Token": "wrong"}, json={})
    assert r.status_code in (401, 403)
