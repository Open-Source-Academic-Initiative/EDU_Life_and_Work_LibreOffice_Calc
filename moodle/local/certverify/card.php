<?php
// This file is part of Moodle - http://moodle.org/  (GPL v3 or later)

/**
 * 1200×630 PNG preview card (Open Graph image) for a PASSED certificate. Name + course + "Aprobado" only.
 * Rendered with GD + bundled DejaVu fonts, cached in localcachedir per certificate version.
 *
 * @package    local_certverify
 */

define('NO_MOODLE_COOKIES', true);
require(__DIR__ . '/../../config.php');

use local_certverify\lookup;
use local_certverify\share;

$serial = lookup::clean_serial(required_param('serial', PARAM_RAW_TRIMMED));
$cert = lookup::is_valid_format($serial) ? lookup::find($serial) : null;
if (!share::shareable($cert)) {
    http_response_code(404);
    die();
}

$cachedir = make_localcache_directory('local_certverify');
$file = $cachedir . '/' . sha1($cert->serial . '|' . $cert->sha256 . '|' . $cert->fullname . '|' . share::CARD_VERSION) . '.png';
// Never cache a card drawn with unresolved strings ("[[key]]", e.g. right after a deploy with a stale string cache).
$stringsok = strpos(get_string('sharecardkicker', 'local_certverify') . get_string('sharecardline', 'local_certverify'),
    '[[') === false;

if (!$stringsok || !is_readable($file)) {
    $w = 1200; $h = 630;
    $fonts = __DIR__ . '/fonts';
    $regular = "$fonts/DejaVuSans.ttf";
    $bold = "$fonts/DejaVuSans-Bold.ttf";
    $im = imagecreatetruecolor($w, $h);
    $white = imagecolorallocate($im, 255, 255, 255);
    $blue = imagecolorallocate($im, 14, 135, 204);      // OpenSAI blue (certificate frame)
    $dark = imagecolorallocate($im, 34, 40, 49);
    $grey = imagecolorallocate($im, 96, 104, 115);
    $green = imagecolorallocate($im, 30, 125, 52);
    $greenbg = imagecolorallocate($im, 228, 244, 232);
    imagefill($im, 0, 0, $white);
    imagefilledrectangle($im, 0, 0, $w, 14, $blue);
    imagefilledrectangle($im, 0, $h - 14, $w, $h, $blue);
    imagesetthickness($im, 2);
    imagerectangle($im, 24, 34, $w - 25, $h - 35, $blue);

    // Centered single line, shrinking the font until it fits.
    $center = function(string $text, string $font, float $size, int $y, $color, int $maxw = 1060) use ($im, $w) {
        do {
            $box = imagettfbbox($size, 0, $font, $text);
            $tw = $box[2] - $box[0];
            if ($tw <= $maxw || $size <= 14) {
                break;
            }
            $size -= 1;
        } while (true);
        imagettftext($im, $size, 0, (int) (($w - $tw) / 2), $y, $color, $font, $text);
    };
    // Up to two centered lines (word wrap), for long course names.
    $wrap = function(string $text, string $font, float $size, int $y, $color, int $maxw = 1000) use ($center) {
        $words = preg_split('/\s+/u', $text);
        $lines = ['']; $i = 0;
        foreach ($words as $word) {
            $try = trim($lines[$i] . ' ' . $word);
            $box = imagettfbbox($size, 0, $font, $try);
            if ($box[2] - $box[0] > $maxw && $lines[$i] !== '' && $i === 0) {
                $lines[++$i] = $word;
            } else {
                $lines[$i] = $try;
            }
        }
        foreach ($lines as $n => $line) {
            $center($line, $font, $size, $y + $n * (int) ($size * 1.5), $color, $maxw + 60);
        }
        return count($lines);
    };

    $logo = @imagecreatefromjpeg(__DIR__ . '/pix/logo.jpg');
    if ($logo) {
        $lw = 231; $lh = (int) round(imagesy($logo) * $lw / imagesx($logo));
        imagecopyresampled($im, $logo, (int) (($w - $lw) / 2), 52, 0, 0, $lw, $lh, imagesx($logo), imagesy($logo));
        imagedestroy($logo);
    }
    $center(core_text::strtoupper(get_string('sharecardkicker', 'local_certverify')), $bold, 17, 178, $blue);
    $center($cert->fullname, $bold, 50, 262, $dark);
    $center(get_string('sharecardline', 'local_certverify'), $regular, 22, 316, $grey);
    $lines = $wrap('«' . strip_tags($cert->coursename) . '»', $bold, 28, 372, $dark);
    // "APROBADO" pill.
    $py = 372 + ($lines - 1) * 42 + 38;
    $label = core_text::strtoupper(get_string('passed', 'local_certverify'));
    $box = imagettfbbox(20, 0, $bold, $label);
    $pw = $box[2] - $box[0] + 56;
    imagefilledrectangle($im, (int) (($w - $pw) / 2), $py, (int) (($w + $pw) / 2), $py + 46, $greenbg);
    $center($label, $bold, 20, $py + 33, $green);
    [$year, $month, $day] = array_map('intval', explode('-', $cert->issued));
    $date = userdate(make_timestamp($year, $month, $day, 12), get_string('strftimedate', 'langconfig'));
    $center($date . '  ·  campus.opensai.org  ·  #' . share::HASHTAG, $regular, 17, $h - 62, $grey);

    if (!$stringsok) {
        header('Content-Type: image/png');
        header('Cache-Control: no-store');
        imagepng($im);
        imagedestroy($im);
        exit;
    }
    $tmp = $file . '.' . getmypid() . '.tmp';
    imagepng($im, $tmp, 6);
    imagedestroy($im);
    rename($tmp, $file);
}

header('Content-Type: image/png');
header('Cache-Control: public, max-age=86400');
header('Content-Length: ' . filesize($file));
readfile($file);
