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

namespace local_certverify;

/**
 * Finds certificates recorded by the SCORM course in the tracking data.
 *
 * When the course issues a certificate it records it in two places of the
 * learner's SCORM tracking data (stored by Moodle per user and attempt):
 *   - cmi.comments:     OSAICERT|1|<serial>|<YYYY-MM-DD>|<grade>|<P|N>|<sha256>|<md5>;
 *   - cmi.suspend_data: JSON with "c" (current certificate) and "h" (history of issued ones)
 * cmi.comments is appended in memory by Moodle's SCORM runtime, so a stale
 * browser tab can overwrite it; suspend_data is the fallback. Either way the
 * serial leads back to the Moodle account (whose full name is shown) and to
 * the SCORM activity.
 *
 * @package    local_certverify
 * @copyright  2026 Open Source Academic Initiative (OpenSAI)
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
class lookup {

    /** Serial format issued by the course, e.g. OSAI-7K2Q-M9XD-4TPA. */
    const SERIAL_PATTERN = '/^[A-Z0-9]{2,10}-[0-9A-Z]{4}-[0-9A-Z]{4}-[0-9A-Z]{4}$/';

    /**
     * Normalises user input: upper case, no spaces.
     *
     * @param string $serial
     * @return string
     */
    public static function clean_serial(string $serial): string {
        return strtoupper(preg_replace('/\s+/', '', $serial));
    }

    /**
     * Whether the text looks like a serial issued by the course.
     *
     * @param string $serial
     * @return bool
     */
    public static function is_valid_format(string $serial): bool {
        return (bool) preg_match(self::SERIAL_PATTERN, $serial);
    }

    /**
     * Looks up a certificate by serial.
     *
     * @param string $serial already cleaned
     * @return \stdClass|null certificate data, or null if not found / not valid
     */
    public static function find(string $serial): ?\stdClass {
        global $DB;

        if (!self::is_valid_format($serial)) {
            return null;
        }
        $like = $DB->sql_like('v.value', ':pattern', false, false);
        $sql = "SELECT v.id, e.element, v.value, v.timemodified, a.userid, a.scormid
                  FROM {scorm_scoes_value} v
                  JOIN {scorm_element} e ON e.id = v.elementid
                  JOIN {scorm_attempt} a ON a.id = v.attemptid
                 WHERE e.element IN ('cmi.comments', 'cmi.suspend_data') AND $like
              ORDER BY v.timemodified DESC";
        $records = $DB->get_records_sql($sql, ['pattern' => '%' . $DB->sql_like_escape($serial) . '%'], 0, 10);

        // Prefer the cmi.comments record, fall back to suspend_data.
        uasort($records, function($a, $b) {
            return ($a->element === 'cmi.comments' ? 0 : 1) <=> ($b->element === 'cmi.comments' ? 0 : 1);
        });
        foreach ($records as $record) {
            $entry = $record->element === 'cmi.comments'
                ? self::parse_entry($record->value, $serial)
                : self::parse_suspend_data($record->value, $serial);
            if ($entry === null) {
                continue;
            }
            $user = \core_user::get_user($record->userid);
            if (!$user || !empty($user->deleted)) {
                return null;
            }
            $scorm = $DB->get_record('scorm', ['id' => $record->scormid], 'id, name, course');
            if (!$scorm) {
                return null;
            }
            $course = get_course($scorm->course);
            $entry->fullname = fullname($user);
            $entry->coursename = format_string($course->fullname, true,
                ['context' => \context_course::instance($course->id)]);
            $entry->activityname = format_string($scorm->name);
            $entry->recorded = (int) $record->timemodified;
            return $entry;
        }
        return null;
    }

    /**
     * Extracts a certificate from the course's suspend_data JSON ("c" = current, "h" = history).
     *
     * @param string $value
     * @param string $serial
     * @return \stdClass|null
     */
    public static function parse_suspend_data(string $value, string $serial): ?\stdClass {
        $data = json_decode($value, true);
        if (!is_array($data)) {
            return null;
        }
        $candidates = [];
        if (!empty($data['c']) && is_array($data['c'])) {
            $candidates[] = $data['c'];
        }
        if (!empty($data['h']) && is_array($data['h'])) {
            $candidates = array_merge($candidates, array_filter($data['h'], 'is_array'));
        }
        foreach ($candidates as $c) {
            if (($c['serial'] ?? null) !== $serial) {
                continue;
            }
            $line = implode('|', ['OSAICERT', '1', $serial, $c['issued'] ?? '', $c['grade'] ?? '',
                !empty($c['passed']) ? 'P' : 'N', $c['sha256'] ?? '', $c['md5'] ?? '']);
            // Same validation as a cmi.comments entry.
            return self::parse_entry($line . ';', $serial);
        }
        return null;
    }

    /**
     * Extracts the certificate entry for a serial from a cmi.comments value
     * (the value may contain several entries separated by ";").
     *
     * @param string $value
     * @param string $serial
     * @return \stdClass|null
     */
    public static function parse_entry(string $value, string $serial): ?\stdClass {
        foreach (preg_split('/;\s*/', $value) as $raw) {
            $p = explode('|', trim($raw));
            if (count($p) < 8 || $p[0] !== 'OSAICERT' || $p[1] !== '1' || $p[2] !== $serial) {
                continue;
            }
            if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $p[3]) || !preg_match('/^[0-9a-f]{64}$/i', $p[6])
                    || !preg_match('/^[0-9a-f]{32}$/i', $p[7])) {
                continue;
            }
            return (object) [
                'serial' => $serial,
                'issued' => $p[3],
                'grade' => (int) $p[4],
                'passed' => $p[5] === 'P',
                'sha256' => strtolower($p[6]),
                'md5' => strtolower($p[7]),
            ];
        }
        return null;
    }
}
