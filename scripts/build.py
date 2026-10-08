"""Build the course: images, content data, SCORM manifest and zip package.

    python3 scripts/build.py            # full build -> dist/Curso_Calc_LaUniversal_SCORM.zip
    python3 scripts/build.py --no-zip   # refresh the package folder only (fast preview)
    python3 scripts/build.py --check    # validate content, write nothing

Inputs
    content/course.json        course text, quizzes (Spanish)
    assets/screenshots/*.png   real LibreOffice captures (capture_screenshots.py)
    assets/manual/*.jpg|png    hand-made screenshots (e.g. web pages, Windows installer)
    assets/photos/*.jpg|png    photos
Outputs (inside curso_calc_universal/, the SCORM package root)
    js/course-data.js          generated from course.json + image sizes
    multimedia/img/*.webp      responsive image variants (800 px and up to 1600 px)
    imsmanifest.xml            SCORM 1.2 manifest listing every packaged file
Requires Pillow (pip install Pillow).
"""

import argparse
import json
import os
import re
import sys
import zipfile
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, "curso_calc_universal")
CONTENT = os.path.join(ROOT, "content", "course.json")
ASSET_DIRS = [os.path.join(ROOT, "assets", d) for d in ("screenshots", "manual", "photos")]
BRAND_DIR = os.path.join(ROOT, "assets", "brand")
IMG_OUT = os.path.join(PKG, "multimedia", "img")
PRACTICE_DIR = os.path.join(PKG, "multimedia", "practica")
DIST = os.path.join(ROOT, "dist")
ZIP_NAME = "Curso_Calc_LaUniversal_SCORM.zip"

WIDTHS = (800, 1600)
WEBP_QUALITY = 82
IMAGE_EXT = (".png", ".jpg", ".jpeg")
# Files inside the package that must never be shipped
EXCLUDE = re.compile(r"(^|/)(\.|originales/|README_IMG\.txt$|.*\.py$)")


def fail(errors):
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(f"\nBuild failed with {len(errors)} error(s).")


# --------------------------------------------------------------- content
def find_asset(name):
    for d in ASSET_DIRS:
        for ext in IMAGE_EXT:
            path = os.path.join(d, name + ext)
            if os.path.exists(path):
                return path
    return None


def inline_errors(text, where):
    errs = []
    for a, b, label in (("**", "**", "bold"), ("[[", "]]", "menu path"), ("{{", "}}", "keys")):
        if a == b:
            if text.count(a) % 2:
                errs.append(f"{where}: unbalanced {label} markup {a}")
        elif text.count(a) != text.count(b):
            errs.append(f"{where}: unbalanced {label} markup {a}{b}")
    if text.count("`") % 2:
        errs.append(f"{where}: unbalanced code markup `")
    return errs


def validate(course):
    errors, images, downloads = [], set(), set()
    unit_ids, slide_ids = set(), set()
    if not course.get("units"):
        errors.append("course has no units")
    cert = course.get("certificate", {})
    for key in ("title", "program", "issuer", "site", "logo", "serialPrefix", "verifyUrl", "textVersion"):
        if not cert.get(key):
            errors.append(f"certificate: missing '{key}'")
    if cert.get("verifyUrl") and "{serial}" not in cert["verifyUrl"]:
        errors.append("certificate.verifyUrl must contain {serial}")
    if cert.get("shareUrl") and "{serial}" not in cert["shareUrl"]:
        errors.append("certificate.shareUrl must contain {serial}")
    if cert.get("logo") and not os.path.exists(os.path.join(BRAND_DIR, cert["logo"] + ".jpg")):
        errors.append(f"certificate logo assets/brand/{cert['logo']}.jpg not found")
    for u in course.get("units", []):
        uid = u.get("id")
        if uid in unit_ids:
            errors.append(f"duplicate unit id {uid}")
        unit_ids.add(uid)
        for key in ("label", "title", "icon", "minutes", "skills", "slides", "quiz"):
            if key not in u:
                errors.append(f"{uid}: missing '{key}'")
        for i, s in enumerate(u.get("slides", [])):
            where = f"{uid} slide {i + 1} ({s.get('id')})"
            if s.get("id") in slide_ids:
                errors.append(f"{where}: duplicate slide id")
            slide_ids.add(s.get("id"))
            if not s.get("title"):
                errors.append(f"{where}: missing title")
            if s.get("image"):
                images.add(s["image"]["src"])
                if not s["image"].get("alt"):
                    errors.append(f"{where}: image without alt text")
                errors += inline_errors(s["image"].get("caption", ""), where + " caption")
            for b in s.get("body", []):
                texts = [b.get("x", "")] + b.get("items", []) + [c for r in b.get("rows", []) for c in r] + b.get("head", [])
                for t in texts:
                    errors += inline_errors(t, where)
                if b.get("t") == "img":
                    images.add(b["src"])
                    if not b.get("alt"):
                        errors.append(f"{where}: inline image without alt text")
                if b.get("t") == "download":
                    downloads.add(b["file"])
        questions = u.get("quiz", {}).get("questions", [])
        if len(questions) < 3:
            errors.append(f"{uid}: quiz needs at least 3 questions")
        for qi, q in enumerate(questions):
            where = f"{uid} question {qi + 1}"
            if not (0 <= q.get("answer", -1) < len(q.get("options", []))):
                errors.append(f"{where}: answer index out of range")
            if len(q.get("options", [])) < 2:
                errors.append(f"{where}: needs 2+ options")
            if not q.get("explain"):
                errors.append(f"{where}: missing explanation")
            for t in [q.get("q", ""), q.get("explain", "")] + q.get("options", []):
                errors += inline_errors(t, where)
            if q.get("image"):
                images.add(q["image"])
    for name in sorted(images):
        if not find_asset(name):
            errors.append(f"image '{name}' not found in assets/(screenshots|manual|photos)")
    for f in sorted(downloads):
        if not os.path.exists(os.path.join(PRACTICE_DIR, f)):
            errors.append(f"practice file '{f}' missing (run scripts/make_practice_files.py)")
    return errors, images


# ---------------------------------------------------------------- images
def build_images(names):
    from PIL import Image
    os.makedirs(IMG_OUT, exist_ok=True)
    meta, keep = {}, set()
    for name in sorted(names):
        src = find_asset(name)
        mtime = os.path.getmtime(src)
        with Image.open(src) as im:
            im = im.convert("RGB")
            w, h = im.size
            widths = sorted({min(w, x) for x in WIDTHS})
            for tw in widths:
                out = os.path.join(IMG_OUT, f"{name}-{tw}.webp")
                keep.add(os.path.basename(out))
                if os.path.exists(out) and os.path.getmtime(out) >= mtime:
                    continue
                th = round(h * tw / w)
                im.resize((tw, th), Image.LANCZOS).save(out, "WEBP", quality=WEBP_QUALITY, method=6)
                print(f"  image {name}-{tw}.webp ({tw}x{th})")
        top = widths[-1]
        meta[name] = {"w": top, "h": round(h * top / w), "widths": widths, "ext": "webp"}
    for f in os.listdir(IMG_OUT):
        path = os.path.join(IMG_OUT, f)
        if os.path.isfile(path) and f not in keep:
            os.remove(path)
            print(f"  removed stale {f}")
    return meta


def write_cert_assets(course):
    """Logo for the PDF certificate as base64 JPEG (baseline RGB, embedded as-is)."""
    import base64
    import io
    from PIL import Image
    src = os.path.join(BRAND_DIR, course["certificate"]["logo"] + ".jpg")
    with Image.open(src) as im:
        im = im.convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=92, progressive=False)
        w, h = im.size
    data = {"logo": {"w": w, "h": h, "b64": base64.b64encode(buf.getvalue()).decode("ascii")}}
    path = os.path.join(PKG, "js", "cert-assets.js")
    body = ("/* GENERATED by scripts/build.py from assets/brand/ — do not edit. */\n"
            "window.CERT_ASSETS = " + json.dumps(data) + ";\n")
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old != body:
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        print("  wrote js/cert-assets.js")


def write_course_data(course, meta):
    path = os.path.join(PKG, "js", "course-data.js")
    body = ("/* GENERATED by scripts/build.py from content/course.json — do not edit. */\n"
            "window.COURSE = " + json.dumps(course, ensure_ascii=False, indent=1) + ";\n"
            "window.COURSE_IMAGES = " + json.dumps(meta, ensure_ascii=False, sort_keys=True) + ";\n")
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old != body:
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        print("  wrote js/course-data.js")


# -------------------------------------------------------------- manifest
def package_files():
    files = []
    for root, dirs, names in os.walk(PKG):
        dirs.sort()
        for n in sorted(names):
            rel = os.path.relpath(os.path.join(root, n), PKG).replace(os.sep, "/")
            if rel == "imsmanifest.xml" or EXCLUDE.search(rel):
                continue
            files.append(rel)
    return files


def write_manifest(course):
    # No adlcp:masteryscore on purpose: with Moodle's default "mastery score
    # overrides status", a partial score mid-course would flip the status to
    # "failed". The player computes passed/failed itself (course.passingScore).
    files = package_files()
    title = escape(course["title"])
    file_tags = "\n".join(f'      <file href="{escape(f)}"/>' for f in files)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GENERATED by scripts/build.py — do not edit. SCORM 1.2 (best supported by Moodle). -->
<manifest identifier="LaUniversalCalc" version="{escape(course['version'])}"
  xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
  xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd http://www.imsglobal.org/xsd/imsmd_rootv1p2p1 imsmd_rootv1p2p1.xsd http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="org_la_universal">
    <organization identifier="org_la_universal">
      <title>{title}</title>
      <item identifier="item_curso" identifierref="res_curso" isvisible="true">
        <title>{title}</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res_curso" type="webcontent" adlcp:scormtype="sco" href="curso_la_universal.html">
{file_tags}
    </resource>
  </resources>
</manifest>
"""
    with open(os.path.join(PKG, "imsmanifest.xml"), "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"  wrote imsmanifest.xml ({len(files)} files)")
    return files


def write_zip(files):
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, ZIP_NAME)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(PKG, "imsmanifest.xml"), "imsmanifest.xml")
        for rel in files:
            z.write(os.path.join(PKG, rel), rel)
    size = os.path.getsize(out) / 1024 / 1024
    print(f"\n✅ SCORM package: {os.path.relpath(out, ROOT)} ({size:.1f} MB, {len(files) + 1} files)")


def bust_cache():
    """Append ?v=<content hash> to the CSS/JS links of the player shell, so a
    browser that cached an older package never mixes old and new files."""
    import hashlib
    shell = os.path.join(PKG, "curso_la_universal.html")
    html = open(shell, encoding="utf-8").read()

    def repl(m):
        path = m.group(2)
        with open(os.path.join(PKG, path), "rb") as f:
            digest = hashlib.sha1(f.read()).hexdigest()[:10]
        return f'{m.group(1)}{path}?v={digest}"'

    new = re.sub(r'((?:href|src)=")((?:css|js)/[\w./-]+\.(?:css|js))(?:\?v=\w+)?"', repl, html)
    if new != html:
        with open(shell, "w", encoding="utf-8") as f:
            f.write(new)
        print("  updated asset versions in curso_la_universal.html")


def write_plugin_zip():
    """Package moodle/local/certverify as an installable Moodle plugin zip
    (Site administration > Plugins > Install plugins)."""
    src = os.path.join(ROOT, "moodle", "local", "certverify")
    if not os.path.isdir(src):
        return
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, "local_certverify.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, names in os.walk(src):
            dirs.sort()
            for n in sorted(names):
                full = os.path.join(root, n)
                z.write(full, os.path.join("certverify", os.path.relpath(full, src)))
    print(f"✅ Moodle plugin:  {os.path.relpath(out, ROOT)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="validate only")
    ap.add_argument("--no-zip", action="store_true", help="skip the zip")
    args = ap.parse_args()

    with open(CONTENT, encoding="utf-8") as f:
        course = json.load(f)
    errors, images = validate(course)
    if errors:
        fail(errors)
    n_slides = sum(len(u["slides"]) for u in course["units"])
    n_q = sum(len(u["quiz"]["questions"]) for u in course["units"])
    print(f"✓ content OK: {len(course['units'])} units, {n_slides} lessons, {n_q} questions, {len(images)} images")
    if args.check:
        return
    meta = build_images(images)
    write_course_data(course, meta)
    write_cert_assets(course)
    bust_cache()
    files = write_manifest(course)
    if not args.no_zip:
        write_zip(files)
        write_plugin_zip()


if __name__ == "__main__":
    main()
