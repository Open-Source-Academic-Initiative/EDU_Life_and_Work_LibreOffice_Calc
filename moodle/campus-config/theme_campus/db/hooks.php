<?php
// Hook callbacks of theme_campus (Moodle 4.4+ hooks API).
// Local, unpublished customization; see OpenSAICampus/README.md for the full log.

defined('MOODLE_INTERNAL') || die();

$callbacks = [
    [
        'hook' => \core\hook\output\before_standard_footer_html_generation::class,
        'callback' => [\theme_campus\hook_callbacks::class, 'before_standard_footer_html_generation'],
    ],
];
