<?php
// This file is part of Moodle - http://moodle.org/  (GPL v3 or later)

/**
 * Social sharing of passed certificates (campaign #EDU_Life_and_Work).
 *
 * Privacy: only PASSED certificates are shareable, and the public share page / preview image show the holder's
 * name, the course and "Aprobado" — never the numeric grade. Sharing is always started by the learner.
 *
 * @package    local_certverify
 */

namespace local_certverify;

defined('MOODLE_INTERNAL') || die();

class share {
    /** Campaign hashtag (without #) and UTM campaign name. */
    const HASHTAG = 'EDU_Life_and_Work';
    /** Issuer as shown by LinkedIn "Add to profile" (an organizationId config value takes precedence). */
    const ORGANIZATION = 'Open Source Academic Initiative';
    /** Bump when the card design/text changes: new image URL → LinkedIn/Facebook fetch it again. */
    const CARD_VERSION = 2;
    /** Brand marks (Simple Icons, CC0) and colours for the share buttons. */
    const LINKEDIN_PATH = 'M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z';
    const FACEBOOK_PATH = 'M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z';
    const LINKEDIN_COLOR = '#0A66C2';
    const FACEBOOK_COLOR = '#1877F2';

    /** Whether a found certificate may be shared. */
    public static function shareable(?\stdClass $cert): bool {
        return $cert !== null && !empty($cert->passed);
    }

    /** Public landing page; $source adds UTM tags so the campaign can be measured. */
    public static function share_url(string $serial, string $source = ''): \moodle_url {
        $params = ['serial' => $serial];
        if ($source !== '') {
            $params += ['utm_source' => $source, 'utm_medium' => 'social', 'utm_campaign' => self::HASHTAG];
        }
        return new \moodle_url('/local/certverify/share.php', $params);
    }

    /** Preview image; the version token busts social-network caches when the certificate is re-issued. */
    public static function card_url(\stdClass $cert): \moodle_url {
        return new \moodle_url('/local/certverify/card.php',
            ['serial' => $cert->serial, 'v' => substr($cert->sha256, 0, 8) . '-' . self::CARD_VERSION]);
    }

    public static function verify_url(string $serial): \moodle_url {
        return new \moodle_url('/local/certverify/index.php', ['serial' => $serial]);
    }

    public static function facebook_url(string $serial): string {
        return 'https://www.facebook.com/sharer/sharer.php?' . http_build_query([
            'u' => self::share_url($serial, 'facebook')->out(false),
            'hashtag' => '#' . self::HASHTAG,
        ], '', '&', PHP_QUERY_RFC3986);
    }

    public static function linkedin_share_url(string $serial): string {
        return 'https://www.linkedin.com/sharing/share-offsite/?' . http_build_query([
            'url' => self::share_url($serial, 'linkedin')->out(false),
        ], '', '&', PHP_QUERY_RFC3986);
    }

    /** LinkedIn "Add to profile" → Licenses & Certifications, with the verification link and serial. */
    public static function linkedin_add_url(\stdClass $cert): string {
        [$year, $month] = array_map('intval', explode('-', $cert->issued));
        $params = [
            'startTask' => 'CERTIFICATION_NAME',
            'name' => $cert->coursename,
            'issueYear' => $year,
            'issueMonth' => $month,
            'certUrl' => self::verify_url($cert->serial)->out(false),
            'certId' => $cert->serial,
        ];
        $orgid = get_config('local_certverify', 'linkedinorgid');
        if ($orgid) {
            $params['organizationId'] = $orgid;
        } else {
            $params['organizationName'] = self::ORGANIZATION;
        }
        return 'https://www.linkedin.com/profile/add?' . http_build_query($params, '', '&', PHP_QUERY_RFC3986);
    }

    /** Short plain-text course description for previews (course summary, trimmed). */
    public static function course_blurb(int $courseid, int $max = 180): string {
        $course = get_course($courseid);
        $context = \context_course::instance($courseid);
        $text = trim(preg_replace('/\s+/u', ' ', html_to_text(format_text($course->summary, $course->summaryformat,
            ['context' => $context]), 0, false)));
        return \core_text::strlen($text) > $max ? rtrim(\core_text::substr($text, 0, $max - 1)) . '…' : $text;
    }

    /** "Nombre completó su sesión de aprendizaje «Curso»". */
    public static function headline(\stdClass $cert): string {
        return get_string('shareheadline', 'local_certverify',
            (object) ['name' => $cert->fullname, 'course' => strip_tags($cert->coursename)]);
    }

    /** Open Graph + Twitter card tags for the share page head. */
    public static function meta_tags(\stdClass $cert): string {
        $title = self::headline($cert);
        $desc = trim(self::course_blurb($cert->courseid) . ' ' .
            get_string('shareinvite', 'local_certverify') . ' #' . self::HASHTAG);
        $image = self::card_url($cert)->out(false);
        $tags = [
            ['property', 'og:type', 'website'],
            ['property', 'og:site_name', 'Campus OpenSAI'],
            ['property', 'og:locale', 'es_CO'],
            ['property', 'og:title', $title],
            ['property', 'og:description', $desc],
            ['property', 'og:url', self::share_url($cert->serial)->out(false)],
            ['property', 'og:image', $image],
            ['property', 'og:image:width', '1200'],
            ['property', 'og:image:height', '630'],
            ['property', 'og:image:alt', $title],
            ['name', 'twitter:card', 'summary_large_image'],
            ['name', 'description', $desc],
        ];
        $html = '';
        foreach ($tags as [$attr, $key, $value]) {
            $html .= '<meta ' . $attr . '="' . s($key) . '" content="' . s($value) . '">' . "\n";
        }
        return $html;
    }

    /** Inline SVG brand mark (no icon font needed). */
    public static function icon(string $path): string {
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="currentColor" ' .
            'aria-hidden="true" focusable="false" style="vertical-align:-3px;margin-right:8px"><path d="' . $path . '"/></svg>';
    }

    /** The three share buttons (used on the verification page), in the networks' brand colours. */
    public static function buttons(\stdClass $cert): string {
        $link = function(string $url, string $label, string $path, string $color) {
            return \html_writer::link($url, self::icon($path) . s($label), ['class' => 'btn me-2 mb-2',
                'style' => "background:$color;border-color:$color;color:#fff;font-weight:600",
                'target' => '_blank', 'rel' => 'noopener']);
        };
        return \html_writer::div(
            $link(self::linkedin_add_url($cert), get_string('sharelinkedinadd', 'local_certverify'),
                self::LINKEDIN_PATH, self::LINKEDIN_COLOR) .
            $link(self::linkedin_share_url($cert->serial), get_string('sharelinkedin', 'local_certverify'),
                self::LINKEDIN_PATH, self::LINKEDIN_COLOR) .
            $link(self::facebook_url($cert->serial), get_string('sharefacebook', 'local_certverify'),
                self::FACEBOOK_PATH, self::FACEBOOK_COLOR),
            'local-certverify-share mb-3');
    }
}
