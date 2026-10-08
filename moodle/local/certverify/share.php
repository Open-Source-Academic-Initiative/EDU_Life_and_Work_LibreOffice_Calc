<?php
// This file is part of Moodle - http://moodle.org/  (GPL v3 or later)

/**
 * Public share landing page for a PASSED certificate (#EDU_Life_and_Work): Open Graph preview for
 * LinkedIn/Facebook + an invitation to take the same learning session. Never shows the numeric grade.
 *
 * @package    local_certverify
 */

require(__DIR__ . '/../../config.php');

use local_certverify\lookup;
use local_certverify\share;

$serial = lookup::clean_serial(required_param('serial', PARAM_RAW_TRIMMED));
$cert = lookup::is_valid_format($serial) ? lookup::find($serial) : null;

$PAGE->set_context(context_system::instance());
$PAGE->set_url(share::share_url($serial));
$PAGE->set_pagelayout('standard');

if (!share::shareable($cert)) {
    $PAGE->set_title(get_string('pagetitle', 'local_certverify'));
    http_response_code(404);
    echo $OUTPUT->header();
    echo $OUTPUT->notification(get_string('notfound', 'local_certverify'), 'error');
    echo $OUTPUT->footer();
    exit;
}

$headline = share::headline($cert);
$PAGE->set_title($headline);
// Open Graph tags for this request only (standard_head_html() prints additionalhtmlhead).
$CFG->additionalhtmlhead = ($CFG->additionalhtmlhead ?? '') . share::meta_tags($cert);

echo $OUTPUT->header();
echo html_writer::start_div('local-certverify-sharepage text-center mx-auto', ['style' => 'max-width: 760px']);
echo html_writer::empty_tag('img', ['src' => share::card_url($cert)->out(false), 'alt' => $headline,
    'class' => 'img-fluid rounded shadow-sm mb-4', 'width' => 1200, 'height' => 630]);
echo html_writer::tag('h2', s($headline), ['class' => 'h4 mb-3']);
$blurb = share::course_blurb($cert->courseid, 400);
if ($blurb !== '') {
    echo html_writer::tag('p', s($blurb), ['class' => 'lead']);
}
echo html_writer::tag('p', get_string('shareinvite', 'local_certverify') . ' ' .
    html_writer::tag('strong', '#' . share::HASHTAG));
echo html_writer::link(new moodle_url('/course/view.php', ['id' => $cert->courseid]),
    get_string('sharecta', 'local_certverify'), ['class' => 'btn btn-primary btn-lg me-2 mb-2']);
echo html_writer::link(share::verify_url($cert->serial), get_string('shareverify', 'local_certverify'),
    ['class' => 'btn btn-outline-secondary btn-lg mb-2']);
echo html_writer::end_div();
echo $OUTPUT->footer();
