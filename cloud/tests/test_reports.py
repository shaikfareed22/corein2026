"""Relay 0.29: a reply the person flags from the app — kept for the operator, ten a day, marked
handled on the admin page; and the support address the public config carries."""

from __future__ import annotations

from test_accounts import auth, make
from test_cloud import sign_up

ADMIN = {"X-Admin-Token": "admin", "X-Admin-Actor": "fareed"}


async def test_a_report_lands_on_the_admin_page_and_is_marked_handled():
    app, client, sender, up, cloud, settings = make(admin_email="ops@example.com")
    assert (await client.get("/v1/config")).json()["support_email"] == "ops@example.com"
    acct = await sign_up(client, sender, "13800138000", "pixel")
    headers = auth(acct["api_key"])

    r = await client.post(
        "/v1/reports",
        headers=headers,
        json={"reason": "wrong", "model": "auto", "text": "The moon is made of cheese. " * 300, "note": "it insisted"},
    )
    assert r.status_code == 204, r.text
    r = await client.post("/v1/reports", headers=headers, json={"reason": "nonsense", "text": "x"})
    assert r.status_code == 400 and "reason" in r.text
    r = await client.post("/v1/reports", headers=headers, json={"reason": "other", "text": "  "})
    assert r.status_code == 400
    r = await client.post("/v1/reports", json={"reason": "other", "text": "x"})
    assert r.status_code == 401

    rv = (await client.get("/v1/admin/reports", headers=ADMIN)).json()
    assert rv["open"] == 1 and rv["per_day"] == 10 and len(rv["reports"]) == 1
    rep = rv["reports"][0]
    assert rep["reason"] == "wrong" and rep["model"] == "auto" and rep["note"] == "it insisted"
    assert len(rep["text"]) == 4000 and rep["resolved_at"] == 0 and rep["account_id"] == acct["account"]["id"]
    assert "138" in rep["hint"]

    r = await client.post(f"/v1/admin/reports/{rep['id']}/resolve", headers=ADMIN, json={})
    assert r.status_code == 200 and r.json()["open"] == 0
    rv = (await client.get("/v1/admin/reports?open=1", headers=ADMIN)).json()
    assert rv["reports"] == []
    rv = (await client.get("/v1/admin/reports", headers=ADMIN)).json()
    assert rv["reports"][0]["resolved_by"] == "fareed" and rv["reports"][0]["resolved_at"] > 0
    assert any(dict(row)["action"] == "report.resolved" and dict(row)["actor"] == "fareed" for row in cloud.db.audit_recent(10))
    r = await client.post(f"/v1/admin/reports/{rep['id']}/resolve", headers=ADMIN, json={"resolved": False})
    assert r.status_code == 200 and r.json()["open"] == 1
    assert (await client.post("/v1/admin/reports/999/resolve", headers=ADMIN, json={})).status_code == 404
    assert (await client.get("/v1/admin/reports")).status_code in (401, 403)


async def test_ten_a_day_per_account():
    app, client, sender, up, cloud, settings = make()
    acct = await sign_up(client, sender, "13800138000", "pixel")
    headers = auth(acct["api_key"])
    for i in range(10):
        assert (await client.post("/v1/reports", headers=headers, json={"reason": "other", "text": f"reply {i}"})).status_code == 204
    r = await client.post("/v1/reports", headers=headers, json={"reason": "other", "text": "one more"})
    assert r.status_code == 429 and r.json()["error"]["code"] == "too_many_reports"
    other = await sign_up(client, sender, "13900139000", "pixel")
    assert (await client.post("/v1/reports", headers=auth(other["api_key"]), json={"reason": "hate", "text": "x"})).status_code == 204
    assert (await client.get("/v1/admin/reports", headers=ADMIN)).json()["open"] == 11
