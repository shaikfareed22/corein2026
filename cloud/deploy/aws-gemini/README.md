# FOMO Cloud on AWS, Gemini for everyone

Your own relay on one AWS free-tier instance, with your Google Gemini key behind it for
every account that signs in. Nothing runs on your laptop: sign-in, the hub the devices meet
on, conversation sync and the web console all live on the instance, and the phone, the
desktop app and any browser point at it. Phone hands work out of the box: the menu names a
Gemini model that reads screenshots in the `gui` lane, and the Android app picks it by
itself.

The relay itself is [`cloud/`](../../README.md); this directory is only what is specific
to AWS and Gemini. It uses the stock `cloud/docker-compose.yml` and `cloud/Caddyfile`.

| | |
|---|---|
| instance | Ubuntu 24.04, free tier (t3.micro or t2.micro, 1 GB; the script adds 2 GB of swap) |
| on the box | `/opt/fomo` (the checkout), `/opt/fomo/cloud/.env` (settings, 0600), `/opt/fomo/cloud/data/cloud.db`, `/opt/fomo/backups/` |
| containers | `relay` (uid 10001 inside, owns `data/`), `caddy` (ports 80 and 443, Let's Encrypt) |
| name | a DuckDNS subdomain; `duckdns.sh` keeps it on the instance every 5 minutes (cron) |
| timers | daily backup 04:10 UTC, 30 days kept; self-check every 10 minutes (`journalctl -t fomo-selfcheck`) |
| models | `gemini-3.5-flash-lite` (chat and hands, the default in both lanes: it answers in about a second on a free-tier key), `gemini-3.8-flash` (stronger, but on a free-tier key it can take minutes and the relay's 180 s wait runs out; pick it with a billed key) |
| settings | `CHAT_DEFAULTS={}` and `CHAT_DROP={"enable_thinking": true, "reasoning_effort": ["none"]}`: Gemini answers 400 to both of those "no thinking" fields, and the phone's hands send one on every screenshot step; `CHAT_TOOL_CALL_SIGNATURE=skip_thought_signature_validator`, Google's placeholder for the thought signature Gemini 3 wants on every earlier tool call in a conversation |
| off | avatar pictures and clips: the relay's image and video routes assume Alibaba's API, so the menu has none and the apps show those features off |

## Before the script: the AWS console and DuckDNS

1. **EC2 → Launch instance.** Ubuntu Server 24.04 LTS, 64-bit x86, a free-tier type
   (`t3.micro` or `t2.micro`), 20 GB of gp3 storage, a key pair you can SSH with.
2. **Security group**, inbound: SSH 22 from your address, HTTP 80 and HTTPS 443 from
   anywhere (0.0.0.0/0). Outbound: all.
3. **Elastic IP.** EC2 → Elastic IPs → Allocate, then Associate with the instance. Without
   it the address changes on every stop/start. It is free while attached to a running
   instance.
4. **DuckDNS.** At https://www.duckdns.org sign in, add a subdomain (say `myfomo`), set
   its *current ip* to the Elastic IP, and copy the token shown at the top of the page.
5. Have ready: your **Gemini API key** (https://aistudio.google.com/apikey), an **SMTP
   mailbox** for the sign-in codes (Gmail: host `smtp.gmail.com`, port 587, your address,
   an *app password* from Google Account → Security), and the e-mail address you will sign
   in with yourself.

## The script

SSH in (`ssh -i key.pem ubuntu@<Elastic IP>`) and run:

```bash
curl -fsSL https://raw.githubusercontent.com/shaikfareed22/corein2026/main/cloud/deploy/aws-gemini/bootstrap.sh \
  | bash -s -- --domain myfomo.duckdns.org --duckdns-token <token>
```

It asks for your e-mail address, the Gemini key and the SMTP settings (the secrets are
typed hidden and never shown), then installs Docker, adds the swap file, clones the
repository under `/opt/fomo`, installs the DuckDNS updater and the timers, writes
`cloud/.env` with fresh random secrets, checks that the name resolves to this instance,
starts the relay and Caddy, and waits for `https://myfomo.duckdns.org/healthz`. The first
certificate takes about a minute after the name resolves. At the end it prints:

```
FOMO Cloud
  console   https://myfomo.duckdns.org/app/
  admin     https://myfomo.duckdns.org/app/admin/   (token in /opt/fomo/cloud/ADMIN_TOKEN.txt)
```

Open the console, sign in with your e-mail address, and the code arrives from your SMTP
mailbox. Your own address is a *member* (no spend limit); everyone else gets the
allowance in `.env` (`ALLOWANCE_CNY`, ¥10 to start, more per invite) on your key.

`bootstrap.sh --help` lists the flags. `--no-start` sets everything up without starting;
`--dry-run` writes the files under a temporary directory and touches nothing else (what
the test suite runs on a laptop).

## Pointing the apps at it

Every app signs in against the community relay unless told otherwise; the devices of one
account must all point at the same relay.

- **Android.** *Use a different server* under the sign-in form → `https://myfomo.duckdns.org`
  → *Check* → *Use this server*.
- **iPhone / iPad.** The same link on the sign-in sheet.
- **Windows / macOS / Linux desktop.** Start the app with
  `NANOMUSE_CLOUD_URL=https://myfomo.duckdns.org` in its environment, or add the
  `nanomuse-cloud` row to `cordis.patch.yml` as [docs/self-hosting.md](../../../docs/self-hosting.md#pointing-the-apps-at-it)
  shows.
- **Any browser.** `https://myfomo.duckdns.org/app/`. Nothing to install.
- **The terminal runtime / a Docker runtime.** `NANOMUSE_CLOUD_BASE_URL=https://myfomo.duckdns.org`.

## Day to day

- **Logs:** `cd /opt/fomo/cloud && sudo docker compose logs -f relay` (and `caddy`).
- **Settings:** edit `/opt/fomo/cloud/.env` with `nano`, then
  `sudo docker compose up -d` in the same directory. The allowance, the invite bonus and
  whether sign-up is open can also be changed on the admin page without a restart.
- **Update:** run the same `curl … | bash -s -- --domain …` line again, or on the box
  `bash /opt/fomo/cloud/deploy/aws-gemini/bootstrap.sh`. Enter keeps every current value;
  secrets and accounts stay. The database schema migrates forward on start.
- **Admin page:** `https://myfomo.duckdns.org/app/admin/`, the token is in
  `/opt/fomo/cloud/ADMIN_TOKEN.txt`: accounts, spend, members, devices on the hub, health.
- **Alerts:** put a webhook that takes `{"text": …}` (Slack, Discord via a bridge, Feishu)
  in `ALERT_URL` in `.env`, and the self-check posts a problem there at most once an hour.

## Backups and restore

`backup.sh` writes `/opt/fomo/backups/cloud-<stamp>.db.gz` every night (a consistent
SQLite copy, taken inside the running container) and a copy of `.env` whenever it changes.
**The database is useless without `CLOUD_SECRET` and the secret is useless without the
database**: keep them together, and copy the newest pair off the instance now and then:

```bash
scp -i key.pem 'ubuntu@<Elastic IP>:/opt/fomo/backups/cloud-*.db.gz' 'ubuntu@<Elastic IP>:/opt/fomo/backups/env.latest' .
```

To restore on a fresh instance: run the bootstrap with `--no-start`, replace
`/opt/fomo/cloud/.env` with the saved one (keep its `CLOUD_SECRET`; update `CLOUD_DOMAIN`
and `PUBLIC_BASE` if the name changed), then

```bash
cd /opt/fomo/cloud && gunzip -c ~/cloud-<stamp>.db.gz | sudo tee data/cloud.db >/dev/null \
  && sudo rm -f data/cloud.db-wal data/cloud.db-shm && sudo chown 10001:10001 data/cloud.db \
  && sudo docker compose up -d --build
```

## What it costs, and the limits

- **AWS.** The free tier covers one small instance, 30 GB of storage and a public IPv4
  address for 750 hours a month in the first 12 months; after that about US$8–10 a month.
  The relay idles well under 200 MB of memory; the model work happens at Google.
- **Gemini.** Every request from every account is billed to your key. The free tier has
  low per-minute and per-day limits that several people together will hit; a billed Google
  Cloud project lifts them. The relay also limits each account to `PER_MINUTE_REQUESTS`
  (30) and to its allowance.
- **Prices in the menu** (`models.json`, in yuan per million tokens at `USD_CNY`) are
  approximations of Google's list prices when this kit was written; they drive the
  allowance ledger, not what Google bills you. Check them against
  https://ai.google.dev/pricing and adjust in `.env` (`CLOUD_MODELS`) as they change.
- **Memory.** 1 GB plus 2 GB of swap is fine for the relay and Caddy. An always-on agent
  runtime (`docker compose up -d app` at the repository root) would also fit, tightly;
  it is not part of this kit.

## Files

| File | |
|---|---|
| `bootstrap.sh` | the one script above; idempotent |
| `env.template` | the settings; `bootstrap.sh` fills the placeholders into `cloud/.env` |
| `models.json` | the `CLOUD_MODELS` menu, one line; `cloud/tests/test_deploy_aws_gemini.py` checks it through the relay's own parser |
| `duckdns.sh`, `fomo-duckdns.cron` | keep the name on the instance |
| `backup.sh`, `fomo-relay-backup.service`, `.timer` | the nightly copy |
| `selfcheck.sh`, `fomo-relay-selfcheck.service`, `.timer` | the ten-minute check |
