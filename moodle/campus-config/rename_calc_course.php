<?php
// Course 8: rename to "Hoja de Cálculo para mi Negocio y mi Trabajo" and replace the SCORM package
// (cmid 51) with the rebuilt one that prints the new name on the certificate.
// Same calls as the activity edit form (mod/scorm/lib.php scorm_update_instance): package file area,
// scorm_parse(), grade item update. Learner tracking is kept (manifest identifiers are unchanged).
// Run inside moodle-app: php rename_calc_course.php /path/to/Curso_Calc_LaUniversal_SCORM.zip
define('CLI_SCRIPT', true);
require('/var/www/html/config.php');
require_once($CFG->dirroot . '/course/lib.php');
require_once($CFG->dirroot . '/mod/scorm/lib.php');
require_once($CFG->dirroot . '/mod/scorm/locallib.php');

$courseid = 8;
$cmid = 51;
$fullname = 'Hoja de Cálculo para mi Negocio y mi Trabajo';
$shortname = 'HCNT';
$activityname = 'Hoja de Cálculo para mi Negocio y mi Trabajo (La Universal)';

$package = $argv[1] ?? '';
if (!is_readable($package)) {
    cli_error("Package not readable: $package");
}

// 1. Course name.
$course = get_course($courseid);
if ($DB->record_exists_select('course', 'shortname = ? AND id <> ?', [$shortname, $courseid])) {
    cli_error("Short name '$shortname' is already used by another course.");
}
mtrace("Course {$course->id}: '{$course->fullname}' ({$course->shortname}) -> '$fullname' ($shortname)");
update_course((object) ['id' => $course->id, 'fullname' => $fullname, 'shortname' => $shortname]);

// 2. SCORM activity: name + package.
$cm = get_coursemodule_from_id('scorm', $cmid, $courseid, false, MUST_EXIST);
$scorm = $DB->get_record('scorm', ['id' => $cm->instance], '*', MUST_EXIST);
$context = context_module::instance($cm->id);
mtrace("SCORM {$scorm->id}: '{$scorm->name}' -> '$activityname'");

$fs = get_file_storage();
$fs->delete_area_files($context->id, 'mod_scorm', 'package');
$fs->create_file_from_pathname([
    'contextid' => $context->id, 'component' => 'mod_scorm', 'filearea' => 'package',
    'itemid' => 0, 'filepath' => '/', 'filename' => basename($package),
], $package);

$DB->update_record('scorm', (object) [
    'id' => $scorm->id, 'name' => $activityname, 'reference' => basename($package), 'timemodified' => time(),
]);
$scorm = $DB->get_record('scorm', ['id' => $scorm->id], '*', MUST_EXIST);
$scorm->course = $courseid;
$scorm->idnumber = $cm->idnumber;
$scorm->cmid = $cm->id;
$oldrevision = $scorm->revision;
scorm_parse($scorm, true);
$scorm = $DB->get_record('scorm', ['id' => $scorm->id], '*', MUST_EXIST);
if ($scorm->version === 'ERROR' || $scorm->revision == $oldrevision) {
    cli_error("Package was not parsed (version '{$scorm->version}', revision {$scorm->revision}).");
}
$scorm->course = $courseid;
$scorm->idnumber = $cm->idnumber;
$scorm->cmid = $cm->id;
scorm_grade_item_update($scorm);

rebuild_course_cache($courseid, true);
mtrace("Package '{$scorm->reference}' parsed: {$scorm->version}, revision {$scorm->revision}, " .
    $DB->count_records('scorm_scoes', ['scorm' => $scorm->id]) . " SCOs.");
