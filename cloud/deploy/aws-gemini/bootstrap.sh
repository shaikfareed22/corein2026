#!/usr/bin/env bash
# FOMO Cloud on an AWS free-tier Ubuntu instance, Google Gemini for every account.
# Run on the instance, once, as a user with sudo; running it again is safe (update,
# re-ask with the current values as defaults, secrets and accounts kept).
#
#   curl -fsSL https://raw.githubusercontent.com/shaikfareed22/corein2026/main/cloud/deploy/aws-gemini/bootstrap.sh \
#     | bash -s -- --domain myname.duckdns.org --duckdns-token XXXX
#
#   --domain NAME          the DuckDNS name (asked when absent)
#   --duckdns-token TOKEN  the DuckDNS token (asked when absent; kept from the last run)
#   --repo URL             where to clone from (default: the FOMO repository)
#   --branch NAME          the branch to follow (default main)
#   --root DIR             where everything lives (default /opt/fomo)
#   --no-start             set everything up, do not start the containers
#   --dry-run              write the files under a temporary root, touch nothing else
#
# What it does, in order: packages (docker, compose, curl, openssl, git); a 2 GB swap
# file; the repository under ROOT; the DuckDNS updater (cron, every 5 minutes); ROOT/cloud/.env
# from env.template with fresh secrets; the backup and self-check timers; a check that the
# name resolves to this instance; docker compose up; a wait for https://NAME/healthz.
# README.md in this directory has the AWS console steps that come before this.
set -euo pipefail

REPO=https://github.com/shaikfareed22/corein2026.git
BRANCH=main
ROOT=/opt/fomo
DOMAIN=""
DUCK_TOKEN=""
START=1
DRY=0
while [ $# -gt 0 ]; do
	case "$1" in
		--domain) DOMAIN="$2"; shift ;;
		--duckdns-token) DUCK_TOKEN="$2"; shift ;;
		--repo) REPO="$2"; shift ;;
		--branch) BRANCH="$2"; shift ;;
		--root) ROOT="$2"; shift ;;
		--no-start) START=0 ;;
		--dry-run) DRY=1 ;;
		-h|--help)
			if [ -f "$0" ]; then sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'
			else echo "flags: --domain NAME --duckdns-token TOKEN [--repo URL] [--branch NAME] [--root DIR] [--no-start] [--dry-run]; see cloud/deploy/aws-gemini/README.md"; fi
			exit 0 ;;
		*) echo "unknown option: $1 (try --help)" >&2; exit 2 ;;
	esac
	shift
done

say() { printf '%s\n' "$*"; }
die() { printf 'bootstrap: %s\n' "$*" >&2; exit 1; }
# where this script lives; `curl | bash` has no BASH_SOURCE, and then only dry-run needs it
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || pwd)"
# the first python that runs (on Windows, a `python3` on the PATH may be the Store's stub)
PY=""
for c in python3 python; do
	if command -v "$c" >/dev/null 2>&1 && "$c" -c 'pass' >/dev/null 2>&1; then PY=$c; break; fi
done
[ -n "$PY" ] || die "python3 is needed (it is on every Ubuntu image)"
SUDO=""
if [ "$DRY" = 0 ] && [ "$(id -u)" != 0 ]; then
	command -v sudo >/dev/null || die "run as root or a user with sudo"
	SUDO=sudo
fi
if [ "$DRY" = 1 ] && [ "$ROOT" = /opt/fomo ]; then
	ROOT=$(mktemp -d "${TMPDIR:-/tmp}/fomo-dry.XXXXXX")
fi
CLOUD="$ROOT/cloud"
ENV_FILE="$CLOUD/.env"
KIT="$CLOUD/deploy/aws-gemini"

# --- asking: answers from the terminal when there is one, else from stdin (tests) -----------
ask() { # ask VAR "prompt" "default"  → plain answer, default kept on Enter
	local var=$1 prompt=$2 default=${3:-} answer
	if [ -n "$default" ]; then prompt="$prompt [$default]"; fi
	if [ -t 0 ] || [ -r /dev/tty ] && [ "$DRY" = 0 ]; then read -r -p "$prompt: " answer </dev/tty
	else read -r answer || answer=""; fi
	printf -v "$var" '%s' "${answer:-$default}"
}
ask_secret() { # ask_secret VAR "prompt" "current"  → hidden; Enter keeps the current one
	local var=$1 prompt=$2 current=${3:-} answer
	if [ -n "$current" ]; then prompt="$prompt [Enter keeps the current one]"; fi
	if [ -t 0 ] || [ -r /dev/tty ] && [ "$DRY" = 0 ]; then read -r -s -p "$prompt: " answer </dev/tty; echo
	else read -r answer || answer=""; fi
	printf -v "$var" '%s' "${answer:-$current}"
}
current() { # current KEY → the value in the existing .env, empty when absent
	[ -f "$ENV_FILE" ] || return 0
	sed -n "s/^$1=//p" "$ENV_FILE" | head -1
}

# --- 1. the box --------------------------------------------------------------------------
require_debian_like() {
	[ "$DRY" = 1 ] && return 0
	[ -r /etc/os-release ] && grep -qiE 'ubuntu|debian' /etc/os-release || die "this script expects Ubuntu or Debian"
}
ensure_packages() {
	[ "$DRY" = 1 ] && { say "dry-run: would install docker.io docker-compose-v2 curl openssl git"; return 0; }
	if ! command -v docker >/dev/null || ! docker compose version >/dev/null 2>&1; then
		say "installing docker and compose"
		$SUDO apt-get update -qq
		DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq docker.io docker-compose-v2 curl openssl git ca-certificates
		$SUDO systemctl enable --now docker
	fi
	if [ -n "$SUDO" ] && ! id -nG | grep -qw docker; then
		$SUDO usermod -aG docker "$USER"
		say "note: $USER was added to the docker group; it applies at your next login (this run uses sudo)"
	fi
}
ensure_swap() {
	[ "$DRY" = 1 ] && { say "dry-run: would create a 2 GB /swapfile"; return 0; }
	if [ "$(swapon --show --noheadings | wc -l)" -gt 0 ]; then return 0; fi
	say "adding a 2 GB swap file (the free tier has 1 GB of memory)"
	$SUDO fallocate -l 2G /swapfile
	$SUDO chmod 600 /swapfile
	$SUDO mkswap -q /swapfile
	$SUDO swapon /swapfile
	grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | $SUDO tee -a /etc/fstab >/dev/null
	echo 'vm.swappiness=10' | $SUDO tee /etc/sysctl.d/90-fomo-swap.conf >/dev/null
	$SUDO sysctl -q -p /etc/sysctl.d/90-fomo-swap.conf
}

# --- 2. the repository -----------------------------------------------------------------
ensure_repo() {
	if [ "$DRY" = 1 ]; then
		# this directory of the checkout the script lives in stands in for the clone
		mkdir -p "$KIT"
		cp "$HERE"/* "$KIT/"
		return 0
	fi
	if [ -d "$ROOT/.git" ]; then
		say "updating $ROOT"
		git -C "$ROOT" fetch -q origin "$BRANCH"
		git -C "$ROOT" checkout -q "$BRANCH"
		git -C "$ROOT" pull -q --ff-only origin "$BRANCH"
	else
		say "cloning $REPO into $ROOT"
		$SUDO mkdir -p "$ROOT"
		$SUDO chown "$(id -u):$(id -g)" "$ROOT"
		git clone -q --branch "$BRANCH" "$REPO" "$ROOT"
	fi
	mkdir -p "$CLOUD/data"
	# the relay runs as uid 10001 in its container and must own the data directory
	$SUDO chown -R 10001:10001 "$CLOUD/data"
}

# --- 3. the name ---------------------------------------------------------------------------
ensure_duckdns() {
	local conf=/opt/fomo/duckdns.conf
	[ "$DRY" = 1 ] && conf="$ROOT/duckdns.conf"
	if [ -z "$DOMAIN" ]; then
		local cur; cur=$(current CLOUD_DOMAIN)
		ask DOMAIN "Your DuckDNS name (myname.duckdns.org)" "$cur"
	fi
	[ -n "$DOMAIN" ] || die "a domain is needed"
	case "$DOMAIN" in *.duckdns.org) ;; *) say "note: $DOMAIN is not a DuckDNS name; the updater is skipped, keep its A record yourself"; return 0 ;; esac
	if [ -z "$DUCK_TOKEN" ]; then
		local cur=""
		[ -r "$conf" ] && cur=$(sed -n 's/^TOKEN=//p' "$conf" | head -1) || true
		[ -n "$cur" ] || { [ "$DRY" = 0 ] && $SUDO test -r "$conf" && cur=$($SUDO sed -n 's/^TOKEN=//p' "$conf" | head -1) || true; }
		ask_secret DUCK_TOKEN "DuckDNS token" "$cur"
	fi
	[ -n "$DUCK_TOKEN" ] || die "a DuckDNS token is needed to keep $DOMAIN pointing here"
	printf 'DOMAIN=%s\nTOKEN=%s\n' "$DOMAIN" "$DUCK_TOKEN" >"$ROOT/duckdns.conf.tmp"
	if [ "$DRY" = 1 ]; then
		mv "$ROOT/duckdns.conf.tmp" "$conf"; chmod 600 "$conf"
		say "dry-run: would install /etc/cron.d/fomo-duckdns and update DuckDNS now"
		return 0
	fi
	$SUDO install -m 600 -o root -g root "$ROOT/duckdns.conf.tmp" "$conf"; rm -f "$ROOT/duckdns.conf.tmp"
	$SUDO install -m 644 "$KIT/fomo-duckdns.cron" /etc/cron.d/fomo-duckdns
	$SUDO chmod 755 "$KIT"/*.sh
	$SUDO "$KIT/duckdns.sh" || die "DuckDNS did not accept the update; check the name and the token"
	say "DuckDNS: $DOMAIN now points at this instance"
}

# --- 4. the settings -------------------------------------------------------------------
write_env() {
	local acme secret admin key smtp_host smtp_port smtp_user smtp_pass smtp_from op_email models
	ask op_email "Your e-mail address (the operator: a member with no limit, Let's Encrypt notices)" "$(current ADMIN_EMAIL)"
	[ -n "$op_email" ] || die "an e-mail address is needed"
	acme=$op_email
	secret=$(current CLOUD_SECRET); [ -n "$secret" ] || secret=$(openssl rand -hex 32)
	admin=$(current CLOUD_ADMIN_TOKEN); [ -n "$admin" ] || admin=$(openssl rand -hex 32)
	ask_secret key "Gemini API key (AIza...)" "$(current UPSTREAM_KEY)"
	[ -n "$key" ] || die "a Gemini key is needed: https://aistudio.google.com/apikey"
	say "Sign-in codes go out by e-mail. Any SMTP mailbox works (Gmail: smtp.gmail.com, 587, an app password)."
	ask smtp_host "SMTP host" "$(current SMTP_HOST)"
	ask smtp_port "SMTP port" "$(current SMTP_PORT)"; smtp_port=${smtp_port:-587}
	ask smtp_user "SMTP user" "$(current SMTP_USER)"
	ask_secret smtp_pass "SMTP password" "$(current SMTP_PASSWORD)"
	ask smtp_from "From address" "$(current SMTP_FROM)"; smtp_from=${smtp_from:-"FOMO <$smtp_user>"}
	[ -n "$smtp_host" ] && [ -n "$smtp_user" ] && [ -n "$smtp_pass" ] || die "the SMTP host, user and password are all needed (CODE_SENDER=smtp)"
	models=$(tr -d '\r\n' <"$KIT/models.json")

	umask 077
	# the values reach python through the environment, never the command line
	FOMO_DOMAIN="$DOMAIN" FOMO_ACME_EMAIL="$acme" FOMO_CLOUD_SECRET="$secret" FOMO_CLOUD_ADMIN_TOKEN="$admin" \
	FOMO_UPSTREAM_KEY="$key" FOMO_OPERATOR_EMAIL="$op_email" FOMO_SMTP_HOST="$smtp_host" FOMO_SMTP_PORT="$smtp_port" \
	FOMO_SMTP_USER="$smtp_user" FOMO_SMTP_PASSWORD="$smtp_pass" FOMO_SMTP_FROM="$smtp_from" FOMO_CLOUD_MODELS="$models" \
	"$PY" - "$KIT/env.template" "$ENV_FILE.new" <<'EOF'
import os, re, sys
src, dst = sys.argv[1], sys.argv[2]
text = open(src, encoding="utf-8").read()
def sub(m):
    name = m.group(1)
    if "FOMO_" + name not in os.environ:
        sys.exit(f"env.template names ${{{name}}}, which bootstrap.sh does not set")
    return os.environ["FOMO_" + name]
out = re.sub(r"\$\{([A-Z_]+)\}", sub, text)
# a value the operator set by hand earlier, outside the template's placeholders, is kept
keep = {}
if os.path.exists(dst[:-4]):
    for line in open(dst[:-4], encoding="utf-8"):
        if "=" in line and not line.startswith("#"):
            k, v = line.rstrip("\n").split("=", 1)
            keep[k] = v
templated = {l.split("=", 1)[0] for l in text.splitlines() if "=" in l and not l.startswith("#")}
extra = [f"{k}={v}" for k, v in keep.items() if k not in templated]
if extra:
    out = out.rstrip("\n") + "\n\n# kept from the previous .env (not in env.template)\n" + "\n".join(extra) + "\n"
open(dst, "w", encoding="utf-8", newline="\n").write(out)
EOF
	mv "$ENV_FILE.new" "$ENV_FILE"
	chmod 600 "$ENV_FILE"
	printf '%s\n' "$admin" >"$CLOUD/ADMIN_TOKEN.txt"; chmod 600 "$CLOUD/ADMIN_TOKEN.txt"
	say "wrote $ENV_FILE"
}

# --- 5. timers ---------------------------------------------------------------------------
install_units() {
	[ "$DRY" = 1 ] && { say "dry-run: would install the backup and self-check timers"; return 0; }
	$SUDO mkdir -p /opt/fomo/backups
	$SUDO chown "$(id -u):$(id -g)" /opt/fomo/backups
	(cd "$KIT" && $SUDO install -m 644 fomo-relay-backup.service fomo-relay-backup.timer fomo-relay-selfcheck.service fomo-relay-selfcheck.timer /etc/systemd/system/)
	$SUDO systemctl daemon-reload
	$SUDO systemctl enable --now fomo-relay-backup.timer fomo-relay-selfcheck.timer >/dev/null
}

# --- 6. does the name reach this box? (before Caddy asks Let's Encrypt for it) ----------------
check_dns() {
	[ "$DRY" = 1 ] && { say "dry-run: would check that $DOMAIN resolves to this instance"; return 0; }
	local mine theirs i
	mine=$(curl -fsS -m 10 https://checkip.amazonaws.com | tr -d '[:space:]' || true)
	[ -n "$mine" ] || { say "note: could not read this instance's public address; skipping the DNS check"; return 0; }
	for i in 1 2 3 4 5 6; do
		theirs=$(getent ahostsv4 "$DOMAIN" | awk 'NR==1 {print $1}' || true)
		[ "$theirs" = "$mine" ] && return 0
		say "waiting for $DOMAIN to resolve to $mine (now: ${theirs:-nothing}) ..."
		sleep 10
	done
	die "$DOMAIN does not resolve to this instance ($mine). Fix the DuckDNS record, then run again; starting now would make Caddy ask Let's Encrypt for a certificate it cannot get"
}

# --- 7. up -----------------------------------------------------------------------------
start() {
	if [ "$DRY" = 1 ] || [ "$START" = 0 ]; then
		say "not starting (${DRY:+dry-run}); later: cd $CLOUD && docker compose up -d --build"
		return 0
	fi
	say "building and starting the relay and Caddy"
	(cd "$CLOUD" && $SUDO docker compose up -d --build --remove-orphans 2>&1 | tail -3)
	local i
	for i in $(seq 1 36); do
		if curl -fsS -m 10 "https://$DOMAIN/healthz" >/dev/null 2>&1; then
			say "up: https://$DOMAIN/healthz answers"
			return 0
		fi
		sleep 5
	done
	say "the relay started but https://$DOMAIN/healthz does not answer yet."
	say "  - the certificate may still be on the way: cd $CLOUD && sudo docker compose logs caddy"
	say "  - ports 80 and 443 must be open in the instance's security group"
	return 1
}

require_debian_like
ensure_packages
ensure_swap
ensure_repo
ensure_duckdns
write_env
install_units
check_dns
start || true

say ""
say "FOMO Cloud"
say "  console   https://$DOMAIN/app/"
say "  admin     https://$DOMAIN/app/admin/   (token in $CLOUD/ADMIN_TOKEN.txt)"
say "  settings  $ENV_FILE"
say "  logs      cd $CLOUD && sudo docker compose logs -f relay"
say "Point the apps at https://$DOMAIN (README.md: Pointing the apps)."
[ "$DRY" = 1 ] && say "dry-run root: $ROOT"
exit 0
