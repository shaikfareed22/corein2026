# AWS Gemini Relay Deploy Kit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A folder `cloud/deploy/aws-gemini/` that turns a fresh AWS free-tier Ubuntu instance into a FOMO Cloud relay serving the operator's Gemini key to every user, with phone hands working, with no code change to the relay.

**Architecture:** The stock `cloud/docker-compose.yml` and `cloud/Caddyfile` run unchanged. The kit adds a settings template with a Gemini-only `CLOUD_MODELS` menu, an idempotent bootstrap script (Docker, swap, DuckDNS, `.env`, compose up, health wait), and backup/self-check timers copied from the Hong Kong kit with paths changed. A pytest proves the menu is well formed through the relay's own parser.

**Tech Stack:** POSIX sh / bash, Docker Compose v2, Caddy 2, systemd timers, cron, pytest.

**Spec:** `docs/superpowers/specs/2026-11-01-aws-gemini-relay-design.md`

## Global Constraints

- No change under `cloud/nanomuse_cloud/`.
- Secrets: read with `read -rs`, never command arguments, never echoed; `.env` mode 0600.
- Relay data dir `cloud/data` owned by uid 10001.
- Repo on the box at `/opt/fomo`; relay at `/opt/fomo/cloud`; backups at `/opt/fomo/backups`.
- `CHAT_DEFAULTS={}`; `UPSTREAM_BASE=https://generativelanguage.googleapis.com/v1beta/openai`; `CLOUD_CATALOG=0`.
- Menu: exactly one model recommended per lane; chat kind only; every model reads images.

## Review Focus

- Re-running `bootstrap.sh` must keep existing `CLOUD_SECRET`; rotating it orphans every account. Test: Task 3 dry-run twice, compare the line.
- `models.json` must survive being inlined on one line in `.env`. Test: Task 1 asserts no newline; Task 3 parses the `.env` line with `json.loads`.
- A domain that does not yet resolve to the instance must stop the bootstrap before Caddy asks Let's Encrypt (rate limits). Task 3 `check_dns`.
- SMTP without `CLOUD_SECRET` makes the relay refuse to start. Bootstrap always writes one (Task 3).
- `selfcheck.sh` hardcodes no domain: it reads `PUBLIC_BASE` from `.env` (Task 2).

---

### Task 1: Gemini menu and settings template, with the test

**Files:**
- Create: `cloud/deploy/aws-gemini/models.json`
- Create: `cloud/deploy/aws-gemini/env.template`
- Test: `cloud/tests/test_deploy_aws_gemini.py`

**Interfaces:**
- Produces: `env.template` with `${PLACEHOLDER}` tokens: `DOMAIN`, `ACME_EMAIL`, `CLOUD_SECRET`, `CLOUD_ADMIN_TOKEN`, `UPSTREAM_KEY`, `OPERATOR_EMAIL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `CLOUD_MODELS`. Task 3 substitutes them.

- [ ] **Step 1: Write the failing test**

```python
import pathlib
from nanomuse_cloud.config import LANES, _models_from_env, menu_warnings

KIT = pathlib.Path(__file__).resolve().parents[1] / "deploy" / "aws-gemini"

def test_menu_is_gemini_chat_only_with_one_pick_per_lane(monkeypatch):
    raw = (KIT / "models.json").read_text()
    assert "\n" not in raw.strip()
    monkeypatch.setenv("CLOUD_MODELS", raw)
    models = _models_from_env()
    assert models and all(m.kind == "chat" for m in models)
    assert all("image" in m.input_modalities for m in models)
    assert all(m.id.startswith("gemini-") for m in models)
    assert menu_warnings(models) == []
    for lane in LANES:
        assert sum(lane in m.recommended_lanes for m in models) == 1

def test_env_template_gemini_settings():
    text = (KIT / "env.template").read_text()
    kv = dict(l.split("=", 1) for l in text.splitlines() if l and not l.startswith("#") and "=" in l)
    assert kv["CHAT_DEFAULTS"] == "{}"
    assert kv["UPSTREAM_BASE"] == "https://generativelanguage.googleapis.com/v1beta/openai"
    assert kv["CLOUD_CATALOG"] == "0"
    assert kv["CODE_SENDER"] == "smtp"
    assert kv["SIGNUP_OPEN"] == "1"
    assert kv["CLOUD_MODELS"] == "${CLOUD_MODELS}"
```

- [ ] **Step 2: Run** `cd cloud && python -m pytest tests/test_deploy_aws_gemini.py -q`. Expected: FAIL, files missing.
- [ ] **Step 3: Write `models.json`** on one line: `gemini-3.8-flash` (for chat+gui, recommended for both, input text+image, price_in 2.1, price_out 17.8) and `gemini-3.5-flash-lite` (for chat+gui, input text+image, in_mult and out_mult 0.3, price_in 0.7, price_out 2.8). Use the real property name for the recommended lanes from `config.py` in the test.
- [ ] **Step 4: Write `env.template`** per the spec's list, every secret as `${NAME}`, brief comments per block.
- [ ] **Step 5: Run the test.** Expected: PASS.
- [ ] **Step 6: Commit** `feat(deploy): aws-gemini menu and settings template`.

### Task 2: DuckDNS updater, backup and self-check

**Files:**
- Create: `cloud/deploy/aws-gemini/duckdns.sh`
- Create: `cloud/deploy/aws-gemini/backup.sh` (from `nanomuse-hk/backup.sh`; defaults `RELAY_DIR=/opt/fomo/cloud`, `BACKUP_DIR=/opt/fomo/backups`; the container through `docker compose exec -T relay`)
- Create: `cloud/deploy/aws-gemini/selfcheck.sh` (from `nanomuse-hk/selfcheck.sh`; `PUBLIC_BASE` read from `.env`; the relay through `docker compose exec -T relay`)
- Create: `fomo-relay-backup.service`, `fomo-relay-backup.timer`, `fomo-relay-selfcheck.service`, `fomo-relay-selfcheck.timer`, `fomo-duckdns.cron`

- [ ] **Step 1: `duckdns.sh`**: reads `/opt/fomo/duckdns.conf` (`DOMAIN=` and `TOKEN=` lines), curls the update URL, appends date and response to `/var/log/fomo-duckdns.log`, exits non-zero when the response is not `OK`.
- [ ] **Step 2: Copy and adapt `backup.sh` and `selfcheck.sh`**; units run `/opt/fomo/cloud/deploy/aws-gemini/*.sh` directly from the checkout.
- [ ] **Step 3: Verify** `bash -n` passes on each script and `grep -l nanomuse-hk *.sh` finds nothing.
- [ ] **Step 4: Commit** `feat(deploy): aws-gemini duckdns, backup and self-check`.

### Task 3: bootstrap.sh

**Files:**
- Create: `cloud/deploy/aws-gemini/bootstrap.sh`

**Interfaces:**
- Consumes: `env.template`, `models.json` (Task 1); scripts and units (Task 2).
- Flags: `--domain`, `--duckdns-token`, `--repo` (default `https://github.com/shaikfareed22/corein2026.git`), `--branch` (default `main`), `--root DIR` (default `/opt/fomo`), `--dry-run`, `--no-start`.

- [ ] **Step 1: Write the script**, functions in this order: parse flags; `require_debian_like` (skipped in dry-run); `ensure_packages` (docker.io, docker-compose-v2, curl, openssl, git; skipped in dry-run); `ensure_swap` (2 GB `/swapfile`, fstab, swappiness 10; skipped in dry-run); `ensure_repo` (clone or `git pull --ff-only`; dry-run uses the checkout the script lives in); `ensure_duckdns` (conf file 0600, cron, first update; network skipped in dry-run); `write_env` (keep existing `CLOUD_SECRET`, `CLOUD_ADMIN_TOKEN`, `UPSTREAM_KEY`, `SMTP_PASSWORD` unless retyped; `openssl rand -hex 32` for new ones; substitution with a small awk/python; `CLOUD_MODELS` from `models.json`; chmod 600; `ADMIN_TOKEN.txt` 0600); `install_units` (skipped in dry-run); `check_dns` (`getent hosts` result equals `https://checkip.amazonaws.com`; skipped in dry-run); `start` (`docker compose up -d --build`, wait up to 180 s for `https://$DOMAIN/healthz`); print URLs.
- [ ] **Step 2: Dry-run** with answers on stdin. Expected: exit 0, the `.env` in the root has no `${` left and its `CLOUD_MODELS` line parses as JSON.
- [ ] **Step 3: Dry-run twice** with the same `--root`; the `CLOUD_SECRET` line is identical.
- [ ] **Step 4: `bash -n bootstrap.sh`** passes. Commit `feat(deploy): aws-gemini bootstrap`.

### Task 4: README and docs

**Files:**
- Create: `cloud/deploy/aws-gemini/README.md`
- Modify: `docs/self-hosting.md` (one sentence under "Your own relay" linking the kit)
- Modify: `CHANGELOG.md` under `[Unreleased]`

- [ ] **Step 1: Write README**: AWS console steps (free-tier instance, Ubuntu 24.04, security group 22/80/443, Elastic IP), DuckDNS, the exact bootstrap command, pointing Android, desktop, browser and runtime at the relay, updating, restoring a backup, costs, Gemini rate limits, the price caveat.
- [ ] **Step 2: Link from `self-hosting.md` and the changelog.** Commit `docs(deploy): aws-gemini kit`.
- [ ] **Step 3: Run** `cd cloud && python -m pytest -q`. Expected: all pass.
