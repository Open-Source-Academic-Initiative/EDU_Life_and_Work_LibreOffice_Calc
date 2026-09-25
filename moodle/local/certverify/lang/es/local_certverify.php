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
 * Spanish strings for local_certverify.
 *
 * @package    local_certverify
 * @copyright  2026 Open Source Academic Initiative (OpenSAI)
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

$string['activity'] = 'Actividad';
$string['badformat'] = 'Eso no parece un serial de certificado. Los seriales tienen la forma OSAI-XXXX-XXXX-XXXX.';
$string['checkbutton'] = 'Comprobar archivo';
$string['checkfile'] = 'Comprobar el archivo PDF';
$string['checkfilehelp'] = 'Sube el PDF del certificado para confirmar que es exactamente el archivo que se expidió (que no fue editado). El archivo solo se lee para calcular su huella digital; no se guarda.';
$string['clihelp'] = 'También puedes comparar las huellas tú mismo: sha256sum archivo.pdf o md5sum archivo.pdf (Linux), certutil -hashfile archivo.pdf SHA256 (Windows).';
$string['course'] = 'Curso';
$string['filematch'] = 'El archivo coincide exactamente con el certificado expedido (SHA-256 y MD5).';
$string['filemissing'] = 'Elige el archivo PDF que quieres comprobar.';
$string['filenomatch'] = 'El archivo NO coincide con el certificado expedido: fue modificado o corresponde a otro serial. SHA-256 del archivo subido: {$a->sha256} · MD5: {$a->md5}';
$string['filetoobig'] = 'El archivo es demasiado grande para ser un certificado de este curso.';
$string['grade'] = 'Nota final';
$string['holder'] = 'Titular';
$string['intro'] = 'Comprueba la autenticidad de un certificado expedido por un curso de OpenSAI. Escribe el serial impreso en el certificado o escanea su código QR.';
$string['issued'] = 'Fecha de expedición';
$string['notfound'] = 'No encontramos un certificado con ese serial. Revisa que esté bien escrito.';
$string['pagetitle'] = 'Verificación de certificados';
$string['participation'] = 'Participación';
$string['passed'] = 'Aprobado';
$string['pluginname'] = 'Verificación de certificados';
$string['privacy:metadata'] = 'El complemento de verificación de certificados no guarda datos personales. Lee los datos de seguimiento SCORM donde se registran los certificados.';
$string['result'] = 'Resultado';
$string['serial'] = 'Serial';
$string['valid'] = 'Certificado válido: fue expedido por este campus.';
$string['verify'] = 'Verificar';
