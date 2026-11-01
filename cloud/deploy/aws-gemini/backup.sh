#!/bin/sh
# Daily copy of the relay's SQLite database, taken with SQLite's own backup API inside the
# running container (consistent under WAL, no stop), gzipped, kept KEEP_DAYS days. Run by
# fomo-relay-backup.timer; harmless by hand.
#
#   RELAY_DIR     where the relay's docker-compose.yml and .env live (default /opt/fomo/cloud)
#   BACKUP_DIR    where copies go (default /opt/fomo/backups)
#   KEEP_DAYS     how many days of copies to keep (default 30)
#   BACKUP_OWNER  who owns the copies, user:group (default: the owner of RELAY_DIR)
#
# A copy is only useful together with CLOUD_SECRET from .env (the identifiers are hashed
# and encrypted with it), so .env is copied alongside whenever it changes, mode 0600.
set -eu

relay=${RELAY_DIR:-/opt/fomo/cloud}
out=${BACKUP_DIR:-/opt/fomo/backups}
keep=${KEEP_DAYS:-30}
owner=${BACKUP_OWNER:-$(stat -c '%u:%g' "$relay")}
stamp=$(date -u +%Y%m%d-%H%M%S)

umask 077
mkdir -p "$out"
chown "$owner" "$out"

# python's sqlite3 backup API inside the relay image (it has the module, not the CLI)
docker compose -f "$relay/docker-compose.yml" --project-directory "$relay" exec -T relay python - "$stamp" <<'EOF'
import sqlite3, sys
src = sqlite3.connect("/srv/nanomuse-cloud/data/cloud.db")
dst = sqlite3.connect(f"/srv/nanomuse-cloud/data/.backup-{sys.argv[1]}.db")
with dst:
    src.backup(dst)
dst.close(); src.close()
EOF
mv "$relay/data/.backup-$stamp.db" "$out/cloud-$stamp.db"
gzip -f "$out/cloud-$stamp.db"
chown "$owner" "$out/cloud-$stamp.db.gz"
chmod 600 "$out/cloud-$stamp.db.gz"

if [ -f "$relay/.env" ] && ! cmp -s "$relay/.env" "$out/env.latest" 2>/dev/null; then
	cp "$relay/.env" "$out/env-$stamp"
	cp "$relay/.env" "$out/env.latest"
	chown "$owner" "$out/env-$stamp" "$out/env.latest"
	chmod 600 "$out/env-$stamp" "$out/env.latest"
fi

find "$out" -name 'cloud-*.db.gz' -mtime +"$keep" -delete
echo "backup: $out/cloud-$stamp.db.gz ($(du -h "$out/cloud-$stamp.db.gz" | cut -f1))"
