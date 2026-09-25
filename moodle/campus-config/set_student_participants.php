<?php
// Privacy: students must not see the course participants list.
// Removes moodle/course:viewparticipants from the Student role definition (all courses)
// and reports any course-level overrides that would still allow it.
define('CLI_SCRIPT', true);
require('/var/www/html/config.php');

$role = $DB->get_record('role', ['shortname' => 'student'], '*', MUST_EXIST);
$cap = 'moodle/course:viewparticipants';
unassign_capability($cap, $role->id, context_system::instance()->id);
$overrides = $DB->get_records_select('role_capabilities', 'roleid = ? AND capability = ? AND permission > 0',
    [$role->id, $cap]);
accesslib_clear_all_caches(true);
mtrace("Removed $cap from role '{$role->shortname}'. Remaining allow overrides: " . count($overrides));
