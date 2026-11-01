# FOMO Cloud on an AWS free-tier instance with Gemini for every user

Date: 2026-11-01. Status: approved in conversation.

## Goal

Run the relay (sign-in, the operator's model key, the hub, conversation sync, the web
console) on one AWS free-tier EC2 instance so that nothing depends on the operator's
laptop. Every account that signs in uses the operator's Google Gemini key through the relay.
Phone hands work out of the box: the relay's menu names a Gemini vision model in the `gui`
lane, which the Android app picks automatically.

## Not in scope

- An always-on agent runtime on the instance (the free tier's 1 GB is tight for it; a later
  add-on).
- Avatar pictures and clips through Gemini. The relay's image and video routes assume
  DashScope; the menu carries no image or video model, so the apps show those features off.
- Changes to the relay's Python code. Everything Alibaba-specific is overridable by settings.

## What the operator does once

1. In the AWS console: launch a free-tier Ubuntu 24.04 instance (t3.micro / t2.micro,
   x86_64), open inbound 22, 80 and 443 in its security group, allocate an Elastic IP and
   attach it.
2. At duckdns.org: create one subdomain, point it at the Elastic IP, note the token.
3. Have ready: the Gemini API key, an SMTP mailbox for sign-in codes (host, port, user,
   password, from address), the operator's own e-mail address.
4. SSH in and run the bootstrap script (below). Fill the four secrets it asks for.

## The kit: `cloud/deploy/aws-gemini/`

Modelled on `cloud/deploy/nanomuse-hk/`, but self-contained on the box: the stock
`cloud/docker-compose.yml` and `cloud/Caddyfile` are used unchanged.

| File | Purpose |
|---|---|
| `README.md` | AWS console steps, DuckDNS, running the bootstrap, pointing each app at the relay, updating, restoring a backup, costs and Gemini rate limits |
| `bootstrap.sh` | One idempotent script run on the instance as a sudoer: installs Docker, a 2 GB swap file, the DuckDNS updater, clones or updates the repo under `/opt/fomo`, writes `cloud/.env` from the template with fresh secrets (kept on re-run), installs the backup and self-check timers, `docker compose up -d --build`, waits for `/healthz` through the public name, prints the URLs |
| `env.template` | The relay settings for Gemini; placeholders for the secrets |
| `models.json` | The `CLOUD_MODELS` menu; inlined into `.env` by the bootstrap, and read by the test |
| `duckdns.sh` | Updates the DuckDNS record from the instance's public address; cron every 5 minutes |
| `backup.sh`, `fomo-relay-backup.service`, `.timer` | Daily consistent SQLite copy, 30 days kept, with `.env` alongside |
| `selfcheck.sh`, `fomo-relay-selfcheck.service`, `.timer` | Every 10 minutes: public `/healthz`, admin health aggregates, free disk, backup age; one journal line |

### bootstrap.sh

- Flags: `--domain NAME.duckdns.org` (asked when absent), `--duckdns-token`, `--repo URL`
  (default this repository), `--branch`, `--dry-run` (write files under a temp dir, start
  nothing), `--no-start`.
- Secrets are read with `read -rs`, never passed as arguments, never echoed. `.env` is 0600.
  Re-running keeps `CLOUD_SECRET`, `CLOUD_ADMIN_TOKEN`, `UPSTREAM_KEY` and the SMTP password
  unless the operator types new ones.
- Swap: `/swapfile` 2 GB, `fstab` entry, `vm.swappiness=10`; skipped if swap exists.
- Docker: the distribution's `docker.io` and `docker-compose-v2` packages; the user is added to
  the `docker` group.
- Data directory `cloud/data` is owned by uid 10001 (the relay's container user).
- Waits up to 3 minutes for `https://<domain>/healthz`, then prints the console
  (`/app/`) and admin (`/app/admin/`) URLs and where the admin token is.

### env.template (the parts that matter)

```
CLOUD_DOMAIN=<domain>
PUBLIC_BASE=https://<domain>
ACME_EMAIL=<operator e-mail>
CLOUD_SECRET=<random>
CLOUD_ADMIN_TOKEN=<random>
UPSTREAM_BASE=https://generativelanguage.googleapis.com/v1beta/openai
UPSTREAM_KEY=<gemini key>
CHAT_DEFAULTS={}
CLOUD_MODELS=<models.json on one line>
CLOUD_CATALOG=0
CLOUD_ANY_MODEL_MEMBERS=1
SIGNUP_OPEN=1
ALLOWED_IDENTIFIERS=<operator e-mail>
ALLOWANCE_CNY=10
INVITE_BONUS_CNY=5
INVITE_URL=https://<domain>/app/?invite=
OWN_KEY_DOCS=https://fomo.corein.in/own-key
OPENROUTER_URL=https://openrouter.ai/keys
PER_MINUTE_REQUESTS=30
CODE_SENDER=smtp
SMTP_HOST=, SMTP_PORT=587, SMTP_USER=, SMTP_PASSWORD=, SMTP_FROM=
HUB_ENABLED=true
DAY_OFFSET_H=0
USD_CNY=7.1
```

`CHAT_DEFAULTS={}` because Gemini rejects `enable_thinking`. `CLOUD_CATALOG=0` keeps the
relay from listing every Gemini model under the key to members; the menu is the offer.

### models.json

Chat models only, lanes set so each lane has exactly one recommended model:

- `gemini-3.8-flash`: `for: ["chat", "gui"]`, `recommended: true`,
  `recommended_for: ["chat", "gui"]`, input `text, image`. The chat default and the hands
  model.
- `gemini-3.5-flash-lite`: `for: ["chat", "gui"]`, input `text, image`, cheaper multipliers
  (`in_mult`/`out_mult` 0.3). The quick option.

Prices in yuan per million tokens are approximations of Google's list prices at 7.1 CNY/USD
and are documented as such in the README; the operator adjusts them in `.env`.

### DuckDNS

`duckdns.sh` curls `https://www.duckdns.org/update?domains=<sub>&token=<token>&ip=` (empty ip
= the caller's address). Token kept in `/opt/fomo/duckdns.token` (0600, root). Cron line in
`/etc/cron.d/fomo-duckdns`, every 5 minutes, output to `/var/log/fomo-duckdns.log`.

## Pointing the apps

- Android: *Use a different server* on the sign-in screen, `https://<domain>`.
- Windows / macOS / Linux desktop: `NANOMUSE_CLOUD_URL=https://<domain>` or the
  `cordis.patch.yml` row, as in `docs/self-hosting.md`.
- Browser: `https://<domain>/app/`.
- Terminal runtime: `NANOMUSE_CLOUD_BASE_URL=https://<domain>`.

## Error handling

- Bootstrap stops with a clear message when: not Ubuntu/Debian, no sudo, the domain does
  not resolve to this instance's public address (DuckDNS not updated yet), port 80/443 not
  reachable from outside after start (likely security group).
- The relay refuses to start without `CLOUD_SECRET` when `CODE_SENDER=smtp`; the bootstrap
  always writes one.
- Self-check posts to `ALERT_URL` when set (optional webhook), otherwise journal only.

## Testing

- `cloud/tests/test_deploy_aws_gemini.py`: loads `models.json` through
  `nanomuse_cloud.config._models_from_env` (via the env var) and asserts: all `kind == "chat"`,
  every model reads images, exactly one model recommended per lane (`menu_warnings` returns
  `[]`), no DashScope ids. Also parses `env.template` and asserts `CHAT_DEFAULTS` is `{}` and
  `UPSTREAM_BASE` is Gemini's.
- `bash bootstrap.sh --dry-run --domain x.duckdns.org` locally in Git Bash writes a complete
  `.env` to a temp dir and exits 0; checked by hand.
- Existing cloud tests keep passing: `cd cloud && python -m pytest -q`.

## Known limits

- Gemini free-tier per-minute limits are low; several users at once hit them. A billed
  Google project lifts this. `PER_MINUTE_REQUESTS` per account is 30.
- Free-tier public IPv4 is free for 750 hours a month in the first year, then billed.
- The instance has 1 GB of memory; the relay and Caddy use well under 200 MB.
