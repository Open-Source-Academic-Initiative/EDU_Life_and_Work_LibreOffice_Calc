<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Moodle is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle.  If not, see <https://www.gnu.org/licenses/>.

/**
 * Public certificate verification page (target of the QR code).
 *
 * Anyone can check a serial, without logging in. Optionally the PDF can be
 * uploaded: its SHA-256 and MD5 are computed on the server and compared with
 * the fingerprints recorded when the certificate was issued. The uploaded file
 * is never stored.
 *
 * @package    local_certverify
 * @copyright  2026 Open Source Academic Initiative (OpenSAI)
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

require(__DIR__ . '/../../config.php');

use local_certverify\lookup;

$serial = lookup::clean_serial(optional_param('serial', '', PARAM_RAW_TRIMMED));
if (!lookup::is_valid_format($serial)) {
    $serialparam = $serial;
    $serial = '';
}

$url = new moodle_url('/local/certverify/index.php', $serial !== '' ? ['serial' => $serial] : []);
$PAGE->set_url($url);
$PAGE->set_context(context_system::instance());
$PAGE->set_pagelayout('standard');
$PAGE->set_title(get_string('pagetitle', 'local_certverify'));
$PAGE->set_heading(get_string('pagetitle', 'local_certverify'));

$certificate = $serial !== '' ? lookup::find($serial) : null;

// Optional file check (POST with sesskey; the file is only read, never saved).
$filecheck = null;
$maxbytes = 10 * 1024 * 1024;
if ($certificate && optional_param('checkfile', 0, PARAM_BOOL) && confirm_sesskey()) {
    $file = $_FILES['certfile'] ?? null;
    if (!$file || $file['error'] !== UPLOAD_ERR_OK || !is_uploaded_file($file['tmp_name'])) {
        $filecheck = ['status' => 'error', 'message' => get_string('filemissing', 'local_certverify')];
    } else if ($file['size'] > $maxbytes) {
        $filecheck = ['status' => 'error', 'message' => get_string('filetoobig', 'local_certverify')];
    } else {
        $sha256 = hash_file('sha256', $file['tmp_name']);
        $md5 = md5_file($file['tmp_name']);
        $matches = hash_equals($certificate->sha256, $sha256) && hash_equals($certificate->md5, $md5);
        $filecheck = ['status' => $matches ? 'match' : 'nomatch', 'sha256' => $sha256, 'md5' => $md5];
    }
    @unlink($file['tmp_name'] ?? '');
}

echo $OUTPUT->header();

echo html_writer::tag('p', get_string('intro', 'local_certverify'));

// Serial form.
echo html_writer::start_tag('form', ['method' => 'get', 'action' => $PAGE->url->out_omit_querystring(),
    'class' => 'd-flex flex-wrap gap-2 align-items-end mb-4']);
echo html_writer::start_div('flex-grow-1');
echo html_writer::label(get_string('serial', 'local_certverify'), 'id_serial', true, ['class' => 'form-label']);
echo html_writer::empty_tag('input', ['type' => 'text', 'name' => 'serial', 'id' => 'id_serial',
    'class' => 'form-control', 'value' => $serial !== '' ? $serial : ($serialparam ?? ''),
    'placeholder' => 'OSAI-XXXX-XXXX-XXXX', 'autocomplete' => 'off', 'spellcheck' => 'false']);
echo html_writer::end_div();
echo html_writer::tag('button', get_string('verify', 'local_certverify'), ['type' => 'submit', 'class' => 'btn btn-primary']);
echo html_writer::end_tag('form');

if (!empty($serialparam)) {
    echo $OUTPUT->notification(get_string('badformat', 'local_certverify'), 'warning');
} else if ($serial !== '' && !$certificate) {
    echo $OUTPUT->notification(get_string('notfound', 'local_certverify'), 'error');
} else if ($certificate) {
    [$year, $month, $day] = array_map('intval', explode('-', $certificate->issued));
    $issued = userdate(make_timestamp($year, $month, $day, 12), get_string('strftimedate', 'langconfig'));
    echo $OUTPUT->notification(get_string('valid', 'local_certverify'), 'success', false);

    $rows = [
        [get_string('holder', 'local_certverify'), s($certificate->fullname)],
        [get_string('course', 'local_certverify'), $certificate->coursename],
        [get_string('activity', 'local_certverify'), $certificate->activityname],
        [get_string('grade', 'local_certverify'), $certificate->grade . ' / 100'],
        [get_string('result', 'local_certverify'),
            get_string($certificate->passed ? 'passed' : 'participation', 'local_certverify')],
        [get_string('issued', 'local_certverify'), $issued],
        [get_string('serial', 'local_certverify'), html_writer::tag('code', s($certificate->serial))],
        ['SHA-256', html_writer::tag('code', $certificate->sha256, ['class' => 'text-break'])],
        ['MD5', html_writer::tag('code', $certificate->md5)],
    ];
    $table = new html_table();
    $table->attributes['class'] = 'generaltable';
    $table->data = array_map(function($r) {
        $head = new html_table_cell($r[0]);
        $head->header = true;
        return new html_table_row([$head, $r[1]]);
    }, $rows);
    echo html_writer::table($table);

    // File integrity check.
    echo $OUTPUT->heading(get_string('checkfile', 'local_certverify'), 3);
    echo html_writer::tag('p', get_string('checkfilehelp', 'local_certverify'));
    if ($filecheck) {
        if ($filecheck['status'] === 'match') {
            echo $OUTPUT->notification(get_string('filematch', 'local_certverify'), 'success', false);
        } else if ($filecheck['status'] === 'nomatch') {
            echo $OUTPUT->notification(get_string('filenomatch', 'local_certverify',
                (object) ['sha256' => $filecheck['sha256'], 'md5' => $filecheck['md5']]), 'error', false);
        } else {
            echo $OUTPUT->notification($filecheck['message'], 'warning', false);
        }
    }
    echo html_writer::start_tag('form', ['method' => 'post', 'enctype' => 'multipart/form-data',
        'action' => $url->out(false), 'class' => 'd-flex flex-wrap gap-2 align-items-center mb-3']);
    echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'sesskey', 'value' => sesskey()]);
    echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'checkfile', 'value' => 1]);
    echo html_writer::empty_tag('input', ['type' => 'file', 'name' => 'certfile', 'accept' => 'application/pdf,.pdf',
        'class' => 'form-control w-auto', 'required' => 'required']);
    echo html_writer::tag('button', get_string('checkbutton', 'local_certverify'),
        ['type' => 'submit', 'class' => 'btn btn-secondary']);
    echo html_writer::end_tag('form');
    echo html_writer::tag('p', get_string('clihelp', 'local_certverify'), ['class' => 'small text-muted']);
}

echo $OUTPUT->footer();
