#!/usr/bin/env bash
# Applies the 2026-10-02 (later) change: certificates issued before the course rename can be
# re-issued with the new name (same serial, date and grade) by downloading them again.
#   - local_certverify 1.2.0: accepts every PDF version recorded for a serial, shows the newest
#   - SCORM package 2.3.0 (via rename_calc_course.php, which is idempotent)
# Run ON nabusimaque as nemqueteba, from this folder (copied there, with
# Curso_Calc_LaUniversal_SCORM.zip and local_certverify.zip next to it):
#   bash apply-reissue.sh
# Logged in OpenSAICampus/README.md.
set -euo pipefail
cd "$(dirname "$0")"
APP=moodle-app
PKG=Curso_Calc_LaUniversal_SCORM.zip
PLUGIN=local_certverify.zip
CODE=~/moodle-campus/moodle-code
STAGE=~/moodle-campus/moodle-data/campus-config-tmp      # moodledata is rw inside the container
IN=/var/www/moodledata/campus-config-tmp
for f in "$PKG" "$PLUGIN" rename_calc_course.php; do
    [ -f "$f" ] || { echo "Missing $f next to this script"; exit 1; }
done

echo "== 1. Database backup"
F=~/moodle-campus-backups/db-before-cert-reissue-$(date +%Y%m%d-%H%M%S).sql.gz
podman exec moodle-db sh -c 'mariadb-dump -uroot -p"$MARIADB_ROOT_PASSWORD" --single-transaction --all-databases' | gzip > "$F"
zcat "$F" | tail -1 | grep -q "Dump completed" && echo "   $F"

echo "== 2. local_certverify 1.2.0 (moodle-code is read-only in the container: install on the host)"
cp -a "$CODE/local/certverify" ~/moodle-campus-backups/local_certverify-before-1.2.0-$(date +%Y%m%d-%H%M%S)
unzip -o -q "$PLUGIN" -d "$CODE/local/"     # overwrites in place: files keep their container_file_t label
ls -Z "$CODE/local/certverify/classes/lookup.php"
podman exec -u www-data $APP php /var/www/html/admin/cli/upgrade.php --non-interactive | tail -2

echo "== 3. SCORM package 2.3.0"
rm -rf "$STAGE"; install -d "$STAGE"; cp rename_calc_course.php "$PKG" "$STAGE/"
podman exec -u www-data $APP php $IN/rename_calc_course.php $IN/$PKG

echo "== 4. Clean up and purge caches"
rm -rf "$STAGE"
podman exec -u www-data $APP php /var/www/html/admin/cli/purge_caches.php
echo "Done."
