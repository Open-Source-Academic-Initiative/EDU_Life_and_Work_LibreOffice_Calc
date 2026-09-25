<?php
// Hook callbacks of theme_campus.
// Local, unpublished customization; see OpenSAICampus/README.md for the full log.

namespace theme_campus;

/**
 * Adds the OpenSAI privacy policy link to the footer help popover ("?").
 * It replaces Moodle's "Resumen de retención de datos" link, which is turned
 * off with tool_dataprivacy | showdataretentionsummary = 0.
 */
class hook_callbacks {
    /** Public privacy policy of OpenSAI. */
    const PRIVACY_URL = 'https://opensai.org/politica-de-privacidad';

    public static function before_standard_footer_html_generation(
        \core\hook\output\before_standard_footer_html_generation $hook
    ): void {
        $link = \html_writer::link(self::PRIVACY_URL, 'Política de privacidad',
            ['target' => '_blank', 'rel' => 'noopener']);
        $hook->add_html(\html_writer::div($link, 'campus-privacy-link'));
    }
}
