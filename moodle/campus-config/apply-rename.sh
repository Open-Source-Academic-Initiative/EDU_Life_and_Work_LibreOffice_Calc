#!/usr/bin/env bash
# Applies the campus.opensai.org changes requested on 2026-10-02:
#   - footer string: "...con ❤️ para el mundo..."
#   - course 8 renamed to "Hoja de Cálculo para mi Negocio y mi Trabajo" (short name HCNT),
#     SCORM package 2.2.0 (new name on new certificates; issued ones stay byte-identical).
# Run ON nabusimaque as nemqueteba, from this folder (copied there, with the package next to it):
#   bash apply-rename.sh
# Standard Moodle mechanisms only (customlang import, course API, SCORM file area + scorm_parse).
# Logged in OpenSAICampus/README.md.
set -euo pipefail
cd "$(dirname "$0")"
APP=moodle-app
PKG=Curso_Calc_LaUniversal_SCORM.zip
STAGE=~/moodle-campus/moodle-data/campus-config-tmp      # moodledata is rw inside the container
IN=/var/www/moodledata/campus-config-tmp
[ -f "$PKG" ] || { echo "Missing $PKG next to this script"; exit 1; }

echo "== 1. Database backup"
F=~/moodle-campus-backups/db-before-calc-rename-$(date +%Y%m%d-%H%M%S).sql.gz
podman exec moodle-db sh -c 'mariadb-dump -uroot -p"$MARIADB_ROOT_PASSWORD" --single-transaction --all-databases' | gzip > "$F"
zcat "$F" | tail -1 | grep -q "Dump completed" && echo "   $F"

echo "== 2. Stage files"
rm -rf "$STAGE"; install -d "$STAGE"; cp -r customlang rename_calc_course.php "$PKG" "$STAGE/"

echo "== 3. Language customisations (es): footer"
podman exec -u www-data $APP php /var/www/html/admin/tool/customlang/cli/import.php --lang=es --source=$IN/customlang/es --checkin

echo "== 4. Rename course 8 + replace SCORM package"
podman exec -u www-data $APP php $IN/rename_calc_course.php $IN/$PKG

echo "== 5. Clean up and purge caches"
rm -rf "$STAGE"
podman exec -u www-data $APP php /var/www/html/admin/cli/purge_caches.php
echo "Done."
