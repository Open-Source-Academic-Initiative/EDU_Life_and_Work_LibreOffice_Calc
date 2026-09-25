#!/usr/bin/env bash
# Applies the campus.opensai.org configuration requested on 2026-09-25.
# Run ON nabusimaque as nemqueteba, from this folder (copied there):  bash apply.sh
# Every change uses a standard Moodle mechanism (cfg.php, customlang import, theme hook,
# role definition, course API). Logged in OpenSAICampus/README.md.
set -euo pipefail
cd "$(dirname "$0")"
APP=moodle-app
CFG="podman exec -u www-data $APP php /var/www/html/admin/cli/cfg.php"
CODE=~/moodle-campus/moodle-code
STAGE=~/moodle-campus/moodle-data/campus-config-tmp      # moodledata is rw inside the container
IN=/var/www/moodledata/campus-config-tmp

echo "== 1. Database backup"
F=~/moodle-campus-backups/db-before-campus-config-$(date +%Y%m%d-%H%M%S).sql.gz
podman exec moodle-db sh -c 'mariadb-dump -uroot -p"$MARIADB_ROOT_PASSWORD" --single-transaction --all-databases' | gzip > "$F"
zcat "$F" | tail -1 | grep -q "Dump completed" && echo "   $F"

echo "== 2. Site settings"
$CFG --name=supportname    --set="OpenSAI"
$CFG --name=supportemail   --set="whiterabbit@opensai.org"
$CFG --name=noreplyaddress --set="whiterabbit@opensai.org"
$CFG --name=supportpage    --set="https://opensai.org/contacto"
$CFG --name=coursecontact  --set=""
$CFG --component=tool_dataprivacy --name=showdataretentionsummary --set=0

echo "== 3. Theme hook (privacy link in the footer help menu)"
install -d "$CODE/theme/campus/db" "$CODE/theme/campus/classes"
install -m 644 theme_campus/db/hooks.php "$CODE/theme/campus/db/hooks.php"
install -m 644 theme_campus/classes/hook_callbacks.php "$CODE/theme/campus/classes/hook_callbacks.php"
# SELinux: `install` labels new files user_home_t (policy default for ~), which the container
# cannot read. Give them the same label as the theme's existing files.
chcon --reference="$CODE/theme/campus/lib.php" "$CODE/theme/campus/db/hooks.php" \
    "$CODE/theme/campus/classes/hook_callbacks.php" "$CODE/theme/campus/db" "$CODE/theme/campus/classes"
sed -i 's/^\$plugin->version   = [0-9]*;/$plugin->version   = 2026092500;/' "$CODE/theme/campus/version.php"
podman exec -u www-data $APP php /var/www/html/admin/cli/upgrade.php --non-interactive | tail -2

echo "== 4. Language customisations (es)"
rm -rf "$STAGE"; install -d "$STAGE"; cp -r customlang set_course_card.php set_student_participants.php course_card_excel.jpg "$STAGE/"
podman exec -u www-data $APP php /var/www/html/admin/tool/customlang/cli/import.php --lang=es --source=$IN/customlang/es --checkin

echo "== 5. Students cannot see participants"
podman exec -u www-data $APP php $IN/set_student_participants.php

echo "== 6. Excel course card (summary + image)"
podman exec -u www-data $APP php $IN/set_course_card.php $IN/course_card_excel.jpg

echo "== 7. Clean up and purge caches"
rm -rf "$STAGE"
podman exec -u www-data $APP php /var/www/html/admin/cli/purge_caches.php
echo "Done."
