#!/bin/sh
# The relay's self-check, every ten minutes (fomo-relay-selfcheck.timer; harmless by hand).
# Reads a few things and writes one line to the journal (journalctl -t fomo-selfcheck):
#
#   GET https://<PUBLIC_BASE>/healthz        the public door answers (PUBLIC_BASE from .env)
#   GET /v1/admin/health inside the container aggregates only: requests under way, the hub's
#                                            counters, the hour's errors, the database
#   df on the relay's volume                 free disk
#   the newest cloud-*.db.gz under BACKUP_DIR backup.sh ran lately
#
# When something is wrong the line is a warning and, with ALERT_URL in .env (any webhook
# that takes a JSON {"text": ...}), the same line is posted there, at most once an hour
# for the same problem.
#
#   RELAY_DIR     where .env lives (default /opt/fomo/cloud)
#   DISK_MIN_MB   warn below this much free (default 1024: the free tier's disk is small)
#   BACKUP_DIR    where backup.sh writes (default /opt/fomo/backups)
#   BACKUP_MAX_H  warn when the newest backup is older than this (default 48)
#   STATE_DIR     once-an-hour state (default /run/fomo-selfcheck)
set -eu

relay=${RELAY_DIR:-/opt/fomo/cloud}
disk_min=${DISK_MIN_MB:-1024}
backups=${BACKUP_DIR:-/opt/fomo/backups}
backup_max_h=${BACKUP_MAX_H:-48}
state=${STATE_DIR:-/run/fomo-selfcheck}
mkdir -p "$state"

public=$(grep '^PUBLIC_BASE=' "$relay/.env" 2>/dev/null | cut -d= -f2- || true)
[ -n "$public" ] || { echo "selfcheck: PUBLIC_BASE missing in $relay/.env" >&2; exit 2; }
# ALERT_URL carries a secret; it reaches python through the environment, never an argument
alert=$(grep '^ALERT_URL=' "$relay/.env" 2>/dev/null | cut -d= -f2- || true)

compose() { docker compose -f "$relay/docker-compose.yml" --project-directory "$relay" "$@"; }

problems=""
add() { problems="${problems}${problems:+; }$1"; }

# 1. the public door
if ! curl -fsS -m 15 "$public/healthz" >/dev/null 2>&1; then
	add "public $public/healthz not answering"
fi

# 2. the relay's own view (the admin token is in the container's environment, from .env)
health=$(compose exec -T relay python -c "
import os, urllib.request
req = urllib.request.Request('http://127.0.0.1:8787/v1/admin/health', headers={'X-Admin-Token': os.environ.get('CLOUD_ADMIN_TOKEN', '')})
print(urllib.request.urlopen(req, timeout=10).read().decode())" 2>/dev/null || true)
if [ -z "$health" ]; then
	add "relay /v1/admin/health not answering"
	summary="(no relay data)"
else
	summary=$(printf '%s' "$health" | python3 -c "
import json, sys
h = json.load(sys.stdin)
hub = h.get('hub') or {}
lh = h.get('last_hour') or {}
inf = h.get('in_flight') or {}
print('v%s hub=%s online/%s accounts; last hour: %s requests, %s upstream errors, %s refused, %s sign-ins (%s failed); in flight %s/%s; db %.1f MB%s' % (
    h.get('version'), hub.get('online'), hub.get('accounts_online'),
    lh.get('requests'), lh.get('upstream_errors'), lh.get('budget_refused'), lh.get('sign_ins'), lh.get('sign_in_failures'),
    inf.get('requests'), inf.get('accounts'), (h.get('db') or {}).get('size_bytes', 0) / 1048576, '' if (h.get('db') or {}).get('writable') else ' NOT WRITABLE'))
for p in h.get('problems') or []:
    print('PROBLEM ' + p)
")
	for p in $(printf '%s\n' "$summary" | sed -n 's/^PROBLEM //p' | tr ' ' '_'); do
		add "$(printf '%s' "$p" | tr '_' ' ')"
	done
	summary=$(printf '%s\n' "$summary" | sed '/^PROBLEM /d')
fi

# 3. the disk the data lives on
free_mb=$(df -Pm "$relay" | awk 'NR==2 {print $4}')
if [ "${free_mb:-0}" -lt "$disk_min" ]; then
	add "only ${free_mb} MB free under $relay"
fi

# 4. the backups
newest=$(ls -t "$backups"/cloud-*.db.gz 2>/dev/null | head -n 1 || true)
if [ -z "$newest" ]; then
	add "no backup yet under $backups"
elif [ -n "$(find "$newest" -mmin +$((backup_max_h * 60)) 2>/dev/null)" ]; then
	add "latest backup $(basename "$newest") is older than ${backup_max_h} hours"
fi

if [ -z "$problems" ]; then
	logger -t fomo-selfcheck -p user.info "ok: $summary"
	rm -f "$state/last-problem"
	exit 0
fi

line="FOMO Cloud self-check: $problems. $summary"
logger -t fomo-selfcheck -p user.warning "$line"
if [ -n "$alert" ]; then
	key=$(printf '%s' "$problems" | md5sum | cut -c1-16)
	if [ ! -f "$state/last-problem" ] || [ "$(cat "$state/last-problem" 2>/dev/null)" != "$key" ] \
		|| [ -n "$(find "$state/last-problem" -mmin +60 2>/dev/null)" ]; then
		printf '%s' "$key" >"$state/last-problem"
		NM_ALERT_URL="$alert" NM_ALERT_TEXT="$line" python3 - <<'EOF' || true
import json, os, urllib.request
url, text = os.environ["NM_ALERT_URL"], os.environ["NM_ALERT_TEXT"]
body = json.dumps({"text": text, "msg_type": "text", "content": {"text": text}}).encode()
req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
urllib.request.urlopen(req, timeout=10).read()
EOF
	fi
fi
exit 1
