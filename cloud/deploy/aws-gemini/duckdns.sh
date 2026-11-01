#!/bin/sh
# Keeps the DuckDNS name pointing at this instance. Run by cron every five minutes
# (fomo-duckdns.cron); harmless by hand. Reads /opt/fomo/duckdns.conf (root, 0600):
#
#   DOMAIN=myname.duckdns.org
#   TOKEN=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
#
# An empty ip= lets DuckDNS use the caller's address, which is the instance's public
# one (the Elastic IP). One line per run goes to /var/log/fomo-duckdns.log.
set -eu

conf=${DUCKDNS_CONF:-/opt/fomo/duckdns.conf}
log=${DUCKDNS_LOG:-/var/log/fomo-duckdns.log}

[ -r "$conf" ] || { echo "duckdns: $conf missing" >&2; exit 2; }
domain=$(sed -n 's/^DOMAIN=//p' "$conf" | head -1)
token=$(sed -n 's/^TOKEN=//p' "$conf" | head -1)
sub=${domain%%.*}
[ -n "$sub" ] && [ -n "$token" ] || { echo "duckdns: DOMAIN or TOKEN missing in $conf" >&2; exit 2; }

# the token travels in the URL, which curl reads from stdin (-K) so it never shows in ps
reply=$(printf 'url = "https://www.duckdns.org/update?domains=%s&token=%s&ip="\n' "$sub" "$token" \
	| curl -fsS -m 20 -K - 2>&1 || true)
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $sub $reply" >>"$log"
[ "$reply" = "OK" ]
