# EDU: Life and Work - LibreOffice Calc for SMEs

## 📌 Context & Motivation

In Colombia and across Latin America (LATAM), millions of micro and small enterprises (SMEs) still rely on paper notebooks to manage their daily operations, inventory, and finances. Transitioning to digital tools is often hindered by the digital divide and the fact that traditional software courses are overly academic, abstract, or targeted at corporate environments.

This repository hosts an open-source, SCORM-compliant micro-course designed specifically for **non-technical human talent** (shopkeepers, hardware store clerks, warehouse assistants, and small business owners).

**The Pedagogical Approach:**
Instead of teaching "Database Normalization" or abstract formulas, this course uses a highly practical, scenario-based narrative. The learner is tasked with helping **"Don Juan,"** the owner of a fictional local hardware store (*Ferretería La Universal*), to migrate his messy paper notebook into **LibreOffice Calc** — the official spreadsheet of LibreOffice, the multiplatform open-source office project (Excel is the spreadsheet of the Microsoft suite).

*Note: While this documentation, the sources and the scripts are in English for international cooperation and development purposes, the actual course content and UI are entirely in **Spanish**, tailored to the LATAM context.*

## 📚 Course content

| Unit | Title (Spanish) | Lessons | Topics |
|------|-----------------|---------|--------|
| 0 | Bienvenida: antes de empezar | 7 | Excel vs. Calc, safe download, install on Windows and Linux, the Calc window, saving (.ods / .xlsx / .pdf) |
| 1 | De la libreta al computador | 7 | Cells, one datum per cell, typing & editing, currency/date formats, column width, freeze row, AutoFormat styles |
| 2 | Que el computador calcule por mí | 7 | `=` formulas, cell references, fill handle, SUMA/PROMEDIO/MAX/MIN/CONTAR, AutoSum, AutoFilter, common errors |
| 3 | Ordenar, resumir y graficar | 7 | Sorting, subtotals and outline levels, SUMAR.SI across sheets, charts (columns, pie) |
| 4 | Limpiando el desastre | 8 | ESPACIOS, NOMPROPIO/MAYUSC/MINUSC, paste values only, text to columns, duplicates, validity lists |

Every unit ends with a graded quiz (5 questions, retakes allowed, best score kept), and completing the course unlocks a downloadable PDF certificate (see below). Units 1–4 include a downloadable practice workbook (`.ods`). All screenshots are **real LibreOffice 25.8 captures with the Spanish UI**, and every menu path, shortcut and function name in the text was checked against LibreOffice itself (e.g. `TRIM` is `ESPACIOS`, Save is `Ctrl+G`, the filter is *Datos ▸ Filtro automático*).

## 📈 Progress tracking & grading (SCORM 1.2)

The package targets **SCORM 1.2**, the version Moodle supports best. The player reports:

| SCORM field | What the course writes |
|-------------|------------------------|
| `cmi.core.lesson_status` | `incomplete` until every lesson is viewed and every quiz attempted; then `passed` (average ≥ 70) or `failed` (retakes can turn it into `passed`) |
| `cmi.core.score.raw` | Average of the best score of each unit quiz (0–100; units not yet attempted count as 0) |
| `cmi.core.lesson_location` | Current lesson, used to resume where the learner left off |
| `cmi.suspend_data` | Compact JSON with the ids of viewed lessons and the best score per unit (under 1 KB, well below the SCORM 1.2 limit of 4,096 characters) |
| `cmi.interactions.n.*` | One record per answered question (`u2-p3`, response, correct pattern, result) for Moodle's interaction reports |
| `cmi.core.session_time`, `cmi.core.exit` | Session length; `suspend` when leaving an unfinished course |

The passing score (70) lives in `content/course.json` (`passingScore`). The manifest deliberately has **no** `adlcp:masteryscore`, so Moodle's "mastery score overrides status" cannot flip a half-finished course to *failed*.

## 🎓 Participation certificate (with QR verification)

When a learner has viewed every lesson and taken all the unit quizzes, the **"Mi progreso"** page offers **"Descargar certificado (PDF)"**. The PDF (A4 landscape) is generated in the browser by `js/certificate.js` (no network, no CDN) and contains:

* the OpenSAI logo (`assets/brand/opensai_logo.jpg`), the program ("Habilidades Digitales para el Trabajo") and the course line ("Curso *Excel* con LibreOffice"),
* the learner's full name from the LMS (`cmi.core.student_name`, "Last, First" → "First Last"); outside an LMS the learner types it,
* the course title and hours, and a table with each unit, its **skills** and the unit's best score,
* the final grade and result (*Aprobado* / *Participación*), issue date and issuer,
* a random **serial** (`OSAI-XXXX-XXXX-XXXX`, 60 bits, Crockford base32) and a **QR code** to the verification page.

All texts live in the `certificate` block of `content/course.json` (`verifyUrl` must contain `{serial}`). The QR encoder is [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) 2.0.4 (MIT), vendored in `js/vendor/qrcode.js`; SHA-256/MD5 are implemented in `js/hash.js`.

### How verification works

1. When the certificate is issued, the course computes the **SHA-256 and MD5** of the exact PDF bytes and writes a record to the learner's SCORM data (`cmi.comments`, which Moodle stores per user and attempt):

       OSAICERT|1|<serial>|<YYYY-MM-DD>|<grade>|<P|N>|<sha256>|<md5>;

2. The serial and date are kept in `suspend_data` (`c` = current certificate, `h` = up to 10 earlier ones), so downloading again produces a **byte-identical** file (same hashes). A new serial is issued only if the grade or the name changes; the earlier serial stays verifiable.
   Moodle's SCORM 1.2 runtime *appends* to `cmi.comments` in the page's memory, so a stale browser tab (e.g. one still running an older package) can overwrite it. Two safeguards: the plugin also finds serials in `suspend_data`, and at each session start the course writes back any issued certificate missing from `cmi.comments` (appending on Moodle, full value on other LMSs).
3. The Moodle plugin **`local_certverify`** (source in `moodle/local/certverify/`, packaged by the build as `dist/local_certverify.zip`) serves the public page `https://campus.opensai.org/local/certverify/index.php?serial=…` (the QR target). It finds the serial in Moodle's SCORM tracking tables (`cmi.comments`, falling back to `cmi.suspend_data`) and shows the holder (from the Moodle account), course, grade, result, date and fingerprints. Anyone can **upload the PDF**: the server hashes it and says whether it matches the issued file (the upload is not stored). People can also compare with `sha256sum` / `md5sum` themselves.

A PDF cannot contain its own hash, which is why the fingerprint is recorded on the campus rather than printed. SHA-256 is the check that matters for tampering; MD5 is shown for convenience (it detects accidental corruption but can be forged deliberately).

Trust model: the certificate is exactly as trustworthy as the SCORM grade itself. The record is written by the course running in the learner's authenticated browser session, like every SCORM score; a technically skilled learner could tamper with their own SCORM data, but not with anyone else's, and not with a certificate that is already recorded. For credentials that need a stronger guarantee, issue them server-side (e.g. Moodle's *Custom certificate* plugin) based on the SCORM completion.

Requirements: Moodle **4.3 or newer** (uses `scorm_attempt` / `scorm_scoes_value` / `scorm_element`; the campus runs 4.5). Install via *Site administration → Plugins → Install plugins* with `dist/local_certverify.zip` — except on **campus.opensai.org**, where the Moodle code is mounted read-only into the container: unzip into `~/moodle-campus/moodle-code/local/` on nabusimaque and run `admin/cli/upgrade.php` inside `moodle-app` (procedure and rollback logged in `../OpenSAICampus/README.md`, 2026-09-25). Only certificates issued by package version ≥ 2.1 are verifiable.

Opened outside an LMS (from disk or any web server) the course runs in **preview mode**: the same data is kept in the browser's `localStorage`, and the summary page offers a button to reset it.

## 🏗️ Technical Architecture

No Node.js/NPM toolchain and no CDNs: the package is plain HTML/CSS/JS and works offline, which matters for learners on slow mobile connections. Python scripts handle screenshots, practice files and packaging.

    EDU_Life_and_Work_LibreOffice_Calc/
    ├── README.md
    ├── content/
    │   └── course.json              # ✏️ SOURCE OF TRUTH: all Spanish text and quizzes
    ├── assets/                      # source images (full resolution)
    │   ├── screenshots/             # real Calc captures (generated, annotated)
    │   ├── manual/                  # hand-made captures (download page, Windows installer…)
    │   └── photos/                  # photos (the paper notebook)
    ├── scripts/
    │   ├── build.py                 # validate content, build images, manifest and zip
    │   ├── capture_screenshots.py   # drive LibreOffice (UNO) and capture real screenshots
    │   ├── make_practice_files.py   # generate the practice .ods workbooks
    │   ├── lo_automation.py         # shared LibreOffice/UNO helpers
    │   └── course_dataset.py        # sample sales data shared by screenshots & practice files
    ├── moodle/local/certverify/     # Moodle plugin: public certificate verification page
    ├── tests/
    │   └── lms_harness.html         # mock SCORM 1.2 LMS for local testing (not shipped)
    ├── curso_calc_universal/        # 📦 SCORM package root (what gets zipped)
    │   ├── curso_la_universal.html  # player shell
    │   ├── css/course.css
    │   ├── js/player.js             # navigation, quizzes, progress, summary
    │   ├── js/scorm.js              # SCORM 1.2 API wrapper + localStorage fallback
│   ├── js/certificate.js        # PDF certificate generator (logo, QR, serial)
│   ├── js/hash.js               # SHA-256 / MD5 of the issued PDF
│   ├── js/cert-assets.js        # ⚙️ generated: logo for the PDF
│   ├── js/vendor/qrcode.js      # QR encoder (MIT, vendored)
    │   ├── js/course-data.js        # ⚙️ generated from content/course.json
    │   ├── imsmanifest.xml          # ⚙️ generated
    │   └── multimedia/
    │       ├── img/                 # ⚙️ generated responsive .webp (800 px + up to 1600 px)
    │       └── practica/            # ⚙️ generated practice workbooks
    ├── build/                       # (ignored) raw captures, LibreOffice scratch profile
    └── dist/                        # (ignored) Curso_Calc_LaUniversal_SCORM.zip

### Content format (`content/course.json`)

Each unit has `slides` (lessons) and a `quiz`. A lesson has a `title`, an optional `image` (`src` = asset name without extension, `alt`, `caption`) and a list of `body` blocks:

| Block `t` | Fields | Renders as |
|-----------|--------|------------|
| `p` | `x` | paragraph |
| `ul` / `steps` / `legend` | `items` | bullet list / numbered step cards / numbered legend matching screenshot badges |
| `tip` / `warn` / `note` | `x` | callout boxes |
| `table` | `head`, `rows` | responsive table |
| `code` | `label`, `x` | terminal/formula block with a copy button |
| `img` | `src`, `alt`, `caption` | extra screenshot |
| `download` | `file`, `label`, `desc` | download card for `multimedia/practica/<file>` |

Inline markup inside any text: `**bold**`, `` `code` ``, `[[Datos ▸ Filtro automático]]` (menu path chip), `{{Ctrl+G}}` (keyboard keys).
Quiz questions: `q`, `options`, `answer` (0-based index; options are shuffled for learners), `explain`, optional `image`.

## 🚀 Workflow

Requirements: Python 3 with **Pillow** (`pip install Pillow`). For screenshots and practice files you also need LibreOffice with the Spanish language pack, Python-UNO, ImageMagick and `wmctrl` (Fedora: `sudo dnf install libreoffice-calc libreoffice-langpack-es python3-libreoffice ImageMagick wmctrl`).

### 1. Edit the content

Change `content/course.json` (never the generated files), then:

    python3 scripts/build.py --no-zip     # validates and refreshes the package folder

The build fails with a clear message on broken references (missing image, missing practice file, bad quiz answer index, unbalanced markup, missing alt text).

### 2. Preview locally

    python3 -m http.server 8765
    # course alone (preview mode):  http://127.0.0.1:8765/curso_calc_universal/curso_la_universal.html
    # inside a mock LMS:            http://127.0.0.1:8765/tests/lms_harness.html

Add `?db=anyname` to the harness URL to start with an empty LMS record. The mock LMS shows the live `lesson_status`, score, location and interaction count, and can reload the course to test resume.

### 3. Screenshots

    python3 scripts/capture_screenshots.py             # capture + annotate everything
    python3 scripts/capture_screenshots.py capture u2_filtro u3_ordenado
    python3 scripts/capture_screenshots.py annotate    # re-crop/re-annotate only (no LibreOffice)

The script starts LibreOffice with a **throwaway profile** (your own profile is never touched), Spanish UI and the X11 backend, builds each scene with the shared sample data, and grabs windows and dialogs at 2× for sharp HiDPI output. Crop boxes and the orange highlight/number badges are defined in `ANNOTATIONS` at the top of the script (raw-pixel coordinates). Windows briefly appear on screen and take keyboard focus; if you type meanwhile, the script detects the stray input and retakes the shot.

Screenshots that cannot be automated (web pages, the Windows installer) go in `assets/manual/` and are referenced by file name like any other image.

### 4. Practice workbooks

    python3 scripts/make_practice_files.py

### 5. Build the SCORM package

    python3 scripts/build.py

Output: `dist/Curso_Calc_LaUniversal_SCORM.zip` (≈3 MB). Images ship as WebP in two widths with `srcset`, so phones download the 800 px version.

## 🌐 Deploying to Moodle (campus.opensai.org)

1. In the course, **Turn editing on → Add an activity or resource → SCORM package**.
2. Upload `dist/Curso_Calc_LaUniversal_SCORM.zip`.
3. Recommended settings:
   - **Appearance:** Display package *Current window*; Width *100 %*; Height *800*; Display course structure on entry page *No*; Show Navigation *No* (the course has its own navigation); Display attempt status *My home and the entry page*.
   - **Grade:** Grading method *Highest grade*; Maximum grade *100*.
   - **Attempts management:** Number of attempts *Unlimited*; Attempts grading *Highest attempt*; Force new attempt *No*.
   - **Compatibility settings:** Mastery score overrides status *No*; Auto-continue *No*.
   - **Activity completion:** *Require status → Passed* (optionally also *Require minimum score 70*).
4. Save, open the activity as a student test account, and check **Reports** after a few lessons: status, score and per-question interactions should appear.

To update the course later, edit the same activity and upload the new zip (Moodle keeps learners' tracking data as long as lesson and unit ids stay the same).

## 🤝 Contribution Guidelines

We welcome contributions from educators, instructional designers, and developers.

* **Content:** If you wish to propose changes to the pedagogical narrative, please submit an issue outlining the educational benefits for LATAM SMEs. Course text stays in Spanish; verify menu paths and function names against a Spanish LibreOffice.
* **Code:** Pull requests should change `content/course.json`, the player (`curso_calc_universal/js|css`) or `scripts/`, never the generated files (`js/course-data.js`, `imsmanifest.xml`, `multimedia/img/`). Keep lesson and unit `id`s stable: learners' saved progress refers to them.

**Maintained by the Open Source Academic Initiative (OpenSAI)**
