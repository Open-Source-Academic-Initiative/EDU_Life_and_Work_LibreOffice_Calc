<?php
// Course 8 ("Excel con Libre Office Calc"): summary + course image, like the other catalog courses.
// Run inside moodle-app: php set_course_card.php /path/to/course_card_excel.jpg
define('CLI_SCRIPT', true);
require('/var/www/html/config.php');
require_once($CFG->dirroot . '/course/lib.php');

$courseid = 8;
$image = $argv[1] ?? '';
if (!is_readable($image)) {
    cli_error("Image not readable: $image");
}
$summary = '<p>Aprende a usar LibreOffice Calc, la alternativa libre y gratuita a Excel, con un caso real: ' .
    'ayudar a don Juan a pasar las ventas de su ferretería de una libreta de papel al computador. En cinco ' .
    'unidades prácticas trabajarás tablas, fórmulas, filtros, gráficos y limpieza de datos, con evaluaciones ' .
    'y un certificado verificable al final.</p>';

$course = get_course($courseid);
update_course((object) ['id' => $course->id, 'summary' => $summary, 'summaryformat' => FORMAT_HTML]);

$context = context_course::instance($course->id);
$fs = get_file_storage();
$fs->delete_area_files($context->id, 'course', 'overviewfiles');
$fs->create_file_from_pathname([
    'contextid' => $context->id, 'component' => 'course', 'filearea' => 'overviewfiles',
    'itemid' => 0, 'filepath' => '/', 'filename' => 'curso_excel_libreoffice.jpg',
], $image);
cache_helper::purge_by_event('changesincourse');
mtrace("Course {$course->id} '{$course->fullname}': summary and image updated.");
