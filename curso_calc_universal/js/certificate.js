/*
 * Participation certificate as a real PDF, generated in the browser.
 *
 * A tiny PDF 1.4 writer using the standard Helvetica and Times fonts with
 * WinAnsi encoding (covers Spanish accents, ñ, «», ¿¡), an embedded JPEG
 * logo and a vector QR code (js/vendor/qrcode.js). Text is measured with the
 * standard AFM widths so it can be centred and wrapped. Works in the LMS and
 * offline; also loadable from Node for tests.
 *
 *   Certificate.build(data)   -> PDF as a binary (latin-1) string
 *   Certificate.toBytes(pdf)  -> Uint8Array
 *   Certificate.save(bytes, filename)
 */
(function (root) {
  "use strict";

  // ---------------------------------------------------------------- metrics
  // Standard AFM widths (1/1000 em) for ASCII 32..126.
  var W = {
    "Helvetica": [278,278,355,556,556,889,667,191,333,333,389,584,278,333,278,278,556,556,556,556,556,556,556,556,556,556,278,278,584,584,584,556,1015,667,667,722,722,667,611,778,722,278,500,667,556,833,722,778,667,778,722,667,611,722,667,944,667,667,611,278,278,278,469,556,333,556,556,500,556,556,278,556,556,222,222,500,222,833,556,556,556,556,333,500,278,556,500,722,500,500,500,334,260,334,584],
    "Helvetica-Bold": [278,333,474,556,556,889,722,238,333,333,389,584,278,333,278,278,556,556,556,556,556,556,556,556,556,556,333,333,584,584,584,611,975,722,722,722,722,667,611,778,722,278,556,722,611,833,722,778,667,778,722,667,611,722,667,944,667,667,611,333,278,333,584,556,333,556,611,556,611,556,333,611,611,278,278,556,278,889,611,611,611,611,389,556,333,611,556,778,556,556,500,389,280,389,584],
    "Times-Bold": [250,333,555,500,500,1000,833,278,333,333,500,570,250,333,250,278,500,500,500,500,500,500,500,500,500,500,333,333,570,570,570,500,930,722,667,722,722,667,611,778,778,389,500,778,667,944,722,778,611,778,722,556,667,722,722,1000,722,722,667,333,278,333,581,500,333,500,556,444,556,444,333,500,556,278,333,556,278,833,556,500,556,556,444,389,333,556,500,722,500,500,444,394,220,394,520],
    "Times-Italic": [250,333,420,500,500,833,778,214,333,333,500,675,250,333,250,278,500,500,500,500,500,500,500,500,500,500,333,333,675,675,675,500,920,611,611,667,722,611,611,722,722,333,444,667,556,833,667,722,611,722,611,500,556,722,611,833,611,556,556,389,278,389,422,500,333,500,500,444,500,444,278,500,500,278,278,444,278,722,500,500,500,500,389,389,278,500,444,667,444,444,389,400,275,400,541]
  };
  W["Helvetica-Oblique"] = W["Helvetica"];
  var FONT_KEYS = { "Helvetica": "F1", "Helvetica-Bold": "F2", "Times-Bold": "F3", "Times-Italic": "F4",
                    "Helvetica-Oblique": "F5" };

  // Accented letters take the width of their base letter.
  var BASE = { "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n",
               "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ü": "U", "Ñ": "N" };
  var CP1252 = { "€": 0x80, "‚": 0x82, "„": 0x84, "…": 0x85, "‘": 0x91, "’": 0x92,
                 "“": 0x93, "”": 0x94, "•": 0x95, "–": 0x96, "—": 0x97, "™": 0x99 };
  var REPLACE = { "▸": ">", "→": "->", "×": "x", "✓": "" };

  function normalize(s) {
    return String(s).replace(/[▸→✓]/g, function (c) { return REPLACE[c]; });
  }

  function charWidth(font, ch) {
    var c = BASE[ch] || ch;
    var code = c.charCodeAt(0);
    if (code >= 32 && code <= 126) return W[font][code - 32];
    if (ch === "«" || ch === "»") return 556;
    if (ch === "¿" || ch === "¡") return 611;
    if (ch === "·") return 278;
    if (ch === "–") return 556;
    if (ch === "—") return 1000;
    return 556;
  }

  function textWidth(font, size, s) {
    s = normalize(s);
    var w = 0;
    for (var i = 0; i < s.length; i++) w += charWidth(font, s.charAt(i));
    return w * size / 1000;
  }

  // PDF literal string, WinAnsi-encoded, ASCII-only via octal escapes.
  function pdfString(s) {
    s = normalize(s);
    var out = "(";
    for (var i = 0; i < s.length; i++) {
      var ch = s.charAt(i), code = s.charCodeAt(i);
      if (CP1252[ch]) code = CP1252[ch];
      else if (code > 255 || (code >= 0x80 && code < 0xA0)) code = 63; // "?"
      if (ch === "(" || ch === ")" || ch === "\\") out += "\\" + ch;
      else if (code < 32 || code > 126) out += "\\" + ("00" + code.toString(8)).slice(-3);
      else out += String.fromCharCode(code);
    }
    return out + ")";
  }

  function wrap(font, size, text, maxWidth) {
    var words = normalize(text).split(/\s+/), lines = [], line = "";
    words.forEach(function (w) {
      var test = line ? line + " " + w : w;
      if (line && textWidth(font, size, test) > maxWidth) { lines.push(line); line = w; }
      else line = test;
    });
    if (line) lines.push(line);
    return lines;
  }

  // ------------------------------------------------------------- page ops
  function Page(w, h) {
    this.w = w; this.h = h; this.ops = [];
  }
  Page.prototype.fill = function (r, g, b) { this.ops.push(r + " " + g + " " + b + " rg"); return this; };
  Page.prototype.stroke = function (r, g, b) { this.ops.push(r + " " + g + " " + b + " RG"); return this; };
  Page.prototype.lineWidth = function (w) { this.ops.push(w + " w"); return this; };
  Page.prototype.rect = function (x, y, w, h, mode) { this.ops.push([x, y, w, h].map(f).join(" ") + " re " + (mode || "f")); return this; };
  Page.prototype.line = function (x1, y1, x2, y2) { this.ops.push(f(x1) + " " + f(y1) + " m " + f(x2) + " " + f(y2) + " l S"); return this; };
  Page.prototype.text = function (font, size, x, y, s, align) {
    var tw = textWidth(font, size, s);
    if (align === "center") x -= tw / 2;
    else if (align === "right") x -= tw;
    this.ops.push("BT /" + FONT_KEYS[font] + " " + size + " Tf " + f(x) + " " + f(y) + " Td " + pdfString(s) + " Tj ET");
    return tw;
  };
  Page.prototype.image = function (name, x, y, w, h) {
    this.ops.push("q " + [w, 0, 0, h, x, y].map(f).join(" ") + " cm /" + name + " Do Q");
    return this;
  };
  // QR code as filled squares; horizontal runs of dark modules become one rect.
  Page.prototype.qr = function (qr, x, y, size) {
    var n = qr.getModuleCount(), m = size / n;
    for (var r = 0; r < n; r++) {
      for (var c = 0; c < n; c++) {
        if (!qr.isDark(r, c)) continue;
        var start = c;
        while (c + 1 < n && qr.isDark(r, c + 1)) c++;
        this.ops.push([x + start * m, y + size - (r + 1) * m, (c - start + 1) * m + 0.02, m + 0.02].map(f).join(" ") + " re f");
      }
    }
    return this;
  };
  // One line mixing fonts, e.g. "Curso " + italic "Excel" + " con LibreOffice"
  Page.prototype.runs = function (runs, size, cx, y) {
    var total = runs.reduce(function (t, r) { return t + textWidth(r.font, size, r.text); }, 0);
    var x = cx - total / 2, self = this;
    runs.forEach(function (r) { x += self.text(r.font, size, x, y, r.text, "left"); });
    return this;
  };
  function f(n) { return (Math.round(n * 100) / 100).toString(); }

  function rgb(hex) {
    var n = parseInt(hex.slice(1), 16);
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255].map(function (v) { return Math.round(v * 1000) / 1000; });
  }

  function assemble(page, images) {
    var fonts = Object.keys(FONT_KEYS);
    images = images || [];
    var objs = [];
    objs.push("<< /Type /Catalog /Pages 2 0 R >>");
    objs.push("<< /Type /Pages /Kids [3 0 R] /Count 1 >>");
    var firstFont = 5, firstImage = firstFont + fonts.length;
    var fontRefs = fonts.map(function (name, i) { return "/" + FONT_KEYS[name] + " " + (firstFont + i) + " 0 R"; }).join(" ");
    var imgRefs = images.map(function (im, i) { return "/" + im.name + " " + (firstImage + i) + " 0 R"; }).join(" ");
    objs.push("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 " + page.w + " " + page.h + "] /Resources << /Font << " +
              fontRefs + " >>" + (images.length ? " /XObject << " + imgRefs + " >>" : "") + " >> /Contents 4 0 R >>");
    var stream = page.ops.join("\n");
    objs.push("<< /Length " + stream.length + " >>\nstream\n" + stream + "\nendstream");
    fonts.forEach(function (name) {
      objs.push("<< /Type /Font /Subtype /Type1 /BaseFont /" + name + " /Encoding /WinAnsiEncoding >>");
    });
    images.forEach(function (im) {
      // JPEG bytes are embedded as-is (DCTDecode); im.data is a binary string
      objs.push("<< /Type /XObject /Subtype /Image /Width " + im.w + " /Height " + im.h +
                " /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length " + im.data.length +
                " >>\nstream\n" + im.data + "\nendstream");
    });
    var info = objs.length + 1;
    objs.push("<< /Producer (OpenSAI - campus.opensai.org) /Title " + pdfString("Certificado de participación") + " >>");

    var out = "%PDF-1.4\n%\u00e2\u00e3\u00cf\u00d3\n", offsets = [];
    objs.forEach(function (o, i) {
      offsets.push(out.length);
      out += (i + 1) + " 0 obj\n" + o + "\nendobj\n";
    });
    var xref = out.length;
    out += "xref\n0 " + (objs.length + 1) + "\n0000000000 65535 f \n";
    offsets.forEach(function (o) { out += ("0000000000" + o).slice(-10) + " 00000 n \n"; });
    out += "trailer\n<< /Size " + (objs.length + 1) + " /Root 1 0 R /Info " + info + " 0 R >>\nstartxref\n" + xref + "\n%%EOF\n";
    return out;
  }

  // -------------------------------------------------------------- layout
  function b64ToBinary(b64) {
    if (typeof atob === "function") return atob(b64);
    return Buffer.from(b64, "base64").toString("latin1"); // Node (tests)
  }

  function makeQR(text) {
    var factory = root.qrcode || (typeof require === "function" ? require("./vendor/qrcode.js") : null);
    if (!factory) return null;
    var qr = factory(0, "M");
    qr.addData(text);
    qr.make();
    return qr;
  }

  /*
   * data: name, title, program, courseLine [{text, italic}], courseTitle,
   *       hours, grade, passed, date, issuer, site, serial, verifyUrl,
   *       units [{label, title, skills[], score}], logo {w, h, b64} (optional)
   */
  function build(data) {
    var P = new Page(842, 595); // A4 landscape, points
    var ink = rgb("#1d2433"), soft = rgb("#4a5468"), blue = rgb("#0192da"), line = rgb("#dfe6ee"),
        paper = rgb("#ffffff"), ok = rgb("#1d7a3e"), band = rgb("#eef6fc");
    var cx = P.w / 2, images = [];

    // background & frame
    P.fill.apply(P, paper).rect(0, 0, P.w, P.h);
    P.stroke.apply(P, blue).lineWidth(2.2).rect(22, 22, P.w - 44, P.h - 44, "S");
    P.stroke.apply(P, line).lineWidth(0.8).rect(30, 30, P.w - 60, P.h - 60, "S");
    P.fill.apply(P, blue).rect(22, P.h - 30, P.w - 44, 8);

    // logo
    var top = P.h - 44;
    if (data.logo) {
      var lh = 46, lw = lh * data.logo.w / data.logo.h;
      images.push({ name: "Im1", w: data.logo.w, h: data.logo.h, data: b64ToBinary(data.logo.b64) });
      P.image("Im1", cx - lw / 2, top - lh, lw, lh);
      top -= lh + 16;
    }

    // program & course
    P.fill.apply(P, blue);
    P.text("Helvetica-Bold", 9.5, cx, top, (data.program || "").toUpperCase(), "center");
    P.fill.apply(P, ink);
    P.runs((data.courseLine || [{ text: data.courseTitle }]).map(function (r) {
      return { font: r.italic ? "Helvetica-Oblique" : "Helvetica", text: r.text };
    }), 13, cx, top - 18);

    // title and name
    P.text("Times-Bold", 27, cx, top - 52, data.title || "Certificado de participación", "center");
    P.fill.apply(P, soft);
    P.text("Helvetica", 11.5, cx, top - 72, "Se certifica que", "center");
    var nameSize = 30;
    while (nameSize > 18 && textWidth("Times-Bold", nameSize, data.name) > 600) nameSize -= 1;
    P.fill.apply(P, ink);
    P.text("Times-Bold", nameSize, cx, top - 104, data.name, "center");
    P.stroke.apply(P, blue).lineWidth(1).line(cx - 190, top - 113, cx + 190, top - 113);

    // statement
    P.fill.apply(P, soft);
    var statement = "participó en el curso «" + data.courseTitle + "», con una intensidad de " + data.hours +
      " horas, desarrollando las competencias que se describen a continuación.";
    wrap("Helvetica", 11, statement, 640).forEach(function (l, i) {
      P.text("Helvetica", 11, cx, top - 133 - i * 14, l, "center");
    });

    // skills table
    var tx = 90, tw = P.w - 180, ty = top - 164, rowH = 30;
    P.fill.apply(P, ink);
    P.text("Helvetica-Bold", 8, tx + 8, ty - 11, "UNIDAD", "left");
    P.text("Helvetica-Bold", 8, tx + 226, ty - 11, "COMPETENCIAS TRABAJADAS", "left");
    P.text("Helvetica-Bold", 8, tx + tw - 8, ty - 11, "NOTA", "right");
    P.stroke.apply(P, ink).lineWidth(0.8).line(tx, ty - 16, tx + tw, ty - 16);
    data.units.forEach(function (u, i) {
      var y = ty - 16 - i * rowH;
      if (i % 2 === 0) P.fill.apply(P, band).rect(tx, y - rowH, tw, rowH);
      P.fill.apply(P, ink);
      wrap("Helvetica-Bold", 8.6, u.label + ". " + u.title, 210).slice(0, 2).forEach(function (l, k) {
        P.text("Helvetica-Bold", 8.6, tx + 8, y - 12 - k * 10, l, "left");
      });
      P.fill.apply(P, soft);
      wrap("Helvetica", 8.2, u.skills.join(" · "), tw - 226 - 58).slice(0, 2).forEach(function (l, k) {
        P.text("Helvetica", 8.2, tx + 226, y - 12 - k * 10, l, "left");
      });
      P.fill.apply(P, ink);
      P.text("Helvetica-Bold", 9.5, tx + tw - 8, y - 17, u.score == null ? "—" : u.score + "/100", "right");
    });
    var tableBottom = ty - 16 - data.units.length * rowH;
    P.stroke.apply(P, line).lineWidth(0.8).line(tx, tableBottom, tx + tw, tableBottom);

    // final grade
    var gy = tableBottom - 28;
    var gradeText = "Nota final: " + data.grade + " / 100";
    var resultText = data.passed ? "Aprobado" : "Participación";
    var gw = textWidth("Helvetica-Bold", 14, gradeText) + textWidth("Helvetica-Bold", 10.5, resultText.toUpperCase()) + 58;
    P.fill.apply(P, data.passed ? rgb("#e7f5ec") : band).rect(cx - gw / 2, gy - 8, gw, 27);
    P.fill.apply(P, ink);
    var gx = cx - gw / 2 + 18;
    gx += P.text("Helvetica-Bold", 14, gx, gy + 1, gradeText, "left") + 22;
    P.fill.apply(P, data.passed ? ok : blue);
    P.text("Helvetica-Bold", 10.5, gx, gy + 2, resultText.toUpperCase(), "left");

    // footer: issue data on the left, QR + serial on the right
    var qrSize = 64, qx = P.w - 90 - qrSize, qy = 38;
    var qr = data.verifyUrl ? makeQR(data.verifyUrl) : null;
    if (qr) {
      P.fill(1, 1, 1).rect(qx - 3, qy - 3, qrSize + 6, qrSize + 6);
      P.fill.apply(P, ink).qr(qr, qx, qy, qrSize);
    }
    P.stroke.apply(P, line).lineWidth(0.8).line(90, qy + qrSize + 8, qx - 14, qy + qrSize + 8);
    P.fill.apply(P, soft);
    P.text("Helvetica", 8.5, 90, qy + 52, "Expedido el " + data.date, "left");
    P.fill.apply(P, ink);
    P.text("Helvetica-Bold", 8.5, 90, qy + 39, data.issuer, "left");
    P.fill.apply(P, soft);
    P.text("Helvetica", 7.4, 90, qy + 26, "Nota final: promedio de las evaluaciones de las " + data.units.length +
      " unidades. Registro en " + data.site + ".", "left");
    P.fill.apply(P, ink);
    P.text("Helvetica-Bold", 9, qx - 14, qy + 30, "Serial: " + data.serial, "right");
    P.fill.apply(P, soft);
    P.text("Helvetica", 7.4, qx - 14, qy + 18, "Escanea el código QR o verifica el serial en", "right");
    P.text("Helvetica", 7.4, qx - 14, qy + 8, (data.verifyUrl || "").replace(/^https?:\/\//, "").replace(/\?.*$/, ""), "right");
    return assemble(P, images);
  }

  function toBytes(bin) {
    var bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i) & 255;
    return bytes;
  }

  function save(bytes, filename) {
    var blob = new Blob([bytes], { type: "application/pdf" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename || "certificado.pdf";
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(url); a.remove(); }, 1500);
  }

  var api = { build: build, toBytes: toBytes, save: save, textWidth: textWidth };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Certificate = api;
})(this);
