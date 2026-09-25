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
 * English strings for local_certverify.
 *
 * @package    local_certverify
 * @copyright  2026 Open Source Academic Initiative (OpenSAI)
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

$string['activity'] = 'Activity';
$string['badformat'] = 'That does not look like a certificate serial. Serials look like OSAI-XXXX-XXXX-XXXX.';
$string['checkbutton'] = 'Check file';
$string['checkfile'] = 'Check the PDF file';
$string['checkfilehelp'] = 'Upload the certificate PDF to confirm it is exactly the file that was issued (it has not been edited). The file is only read to compute its fingerprint; it is not stored.';
$string['clihelp'] = 'You can also compare the fingerprints yourself: sha256sum file.pdf or md5sum file.pdf (Linux), certutil -hashfile file.pdf SHA256 (Windows).';
$string['course'] = 'Course';
$string['filematch'] = 'The file matches the issued certificate exactly (SHA-256 and MD5).';
$string['filemissing'] = 'Choose the PDF file to check.';
$string['filenomatch'] = 'The file does NOT match the issued certificate: it was modified or belongs to a different serial. Uploaded file SHA-256: {$a->sha256} · MD5: {$a->md5}';
$string['filetoobig'] = 'The file is too large to be a certificate from this course.';
$string['grade'] = 'Final grade';
$string['holder'] = 'Holder';
$string['intro'] = 'Check the authenticity of a certificate issued by an OpenSAI course. Enter the serial printed on the certificate, or scan its QR code.';
$string['issued'] = 'Issue date';
$string['notfound'] = 'No certificate was found with that serial. Check it was typed correctly.';
$string['pagetitle'] = 'Certificate verification';
$string['participation'] = 'Participation';
$string['passed'] = 'Passed';
$string['pluginname'] = 'Certificate verification';
$string['privacy:metadata'] = 'The Certificate verification plugin does not store personal data. It reads the SCORM tracking data where certificates are recorded.';
$string['result'] = 'Result';
$string['serial'] = 'Serial';
$string['valid'] = 'Valid certificate: it was issued by this campus.';
$string['verify'] = 'Verify';
