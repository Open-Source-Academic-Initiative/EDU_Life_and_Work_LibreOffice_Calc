"""Capture real LibreOffice Calc screenshots (Spanish UI) for the course.

Two phases:
  capture   drives LibreOffice through UNO and grabs raw windows into
            build/captures/  (needs LibreOffice, ImageMagick, wmctrl, X/XWayland)
  annotate  crops raw captures and draws highlight boxes / numbered badges,
            writing the final images to assets/screenshots/  (needs Pillow only)

Usage:
    python3 scripts/capture_screenshots.py            # both phases
    python3 scripts/capture_screenshots.py capture [shot ...]
    python3 scripts/capture_screenshots.py annotate [shot ...]

Raw captures are taken at 2x (HiDPI) so the web versions stay sharp.
Crop/annotation coordinates below are in raw pixels of those captures.
"""

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "build", "captures")
OUT_DIR = os.path.join(ROOT, "assets", "screenshots")
WORK_DIR = os.path.join(ROOT, "build", "work")

# Calc main window size on screen (2x scale => 1200x750 logical pixels).
WIN_W, WIN_H = 2400, 1500

# ---------------------------------------------------------------------------
# Annotation specs: name -> {"crop": (x0, y0, x1, y1) or None,
#                            "marks": [(x0, y0, x1, y1, label-or-None), ...]}
# Coordinates refer to the raw capture (before cropping).
# ---------------------------------------------------------------------------
ANNOTATIONS = {
    "u0_ventana_calc": {"crop": None, "marks": [
        (2, 0, 1440, 56, "1", (1480, 28)), (0, 60, 2400, 208, "2"),
        (6, 212, 372, 282, "3"), (392, 212, 2272, 282, "4"),
        (90, 336, 254, 376, "5", (300, 356)),
        (0, 958, 404, 1012, "6", (446, 985)), (0, 1014, 2400, 1060, "7", (1330, 1037)),
        (2282, 212, 2400, 720, "8")]},
    "u1_celda_activa": {"crop": (0, 190, 1300, 760), "marks": [
        (6, 212, 372, 282, "1"), (414, 404, 584, 444, "2")]},
    "u1_datos_crudos": {"crop": (0, 190, 1700, 1100), "marks": []},
    "u1_datos_formateados": {"crop": (0, 190, 2280, 1100), "marks": []},
    "u1_tabla_estilo": {"crop": (0, 190, 2280, 1100), "marks": []},
    "u2_formula_simple": {"crop": (0, 190, 1300, 620), "marks": [
        (560, 212, 1300, 282, None)]},
    "u2_formula_referencias": {"crop": (0, 190, 2280, 900), "marks": [
        (560, 212, 1100, 282, None)]},
    "u2_copiar_formula": {"crop": (0, 190, 2280, 1180), "marks": []},
    "u2_funciones": {"crop": (0, 190, 2280, 900), "marks": [
        (560, 212, 1200, 282, None)]},
    "u2_autosuma": {"crop": (0, 190, 1300, 560), "marks": [
        (440, 222, 520, 276, None)]},
    "u2_filtro": {"crop": (0, 190, 2280, 900), "marks": []},
    "u2_error_nombre": {"crop": (0, 190, 1500, 620), "marks": []},
    "u3_ordenado": {"crop": (0, 190, 2280, 1180), "marks": []},
    "u3_subtotales_resultado": {"crop": (0, 190, 2280, 1180), "marks": []},
    "u3_subtotales_nivel2": {"crop": (0, 190, 2280, 900), "marks": []},
    "u3_sumar_si": {"crop": (0, 190, 1700, 760), "marks": [
        (560, 212, 1700, 282, None)]},
    "u3_grafico_columnas": {"crop": (0, 190, 2280, 1200), "marks": []},
    "u3_grafico_circular": {"crop": (0, 190, 2280, 1200), "marks": []},
    "u4_datos_sucios": {"crop": (0, 190, 1500, 900), "marks": []},
    "u4_espacios": {"crop": (0, 190, 2000, 900), "marks": [
        (560, 212, 1300, 282, None)]},
    "u4_nompropio": {"crop": (0, 190, 2000, 900), "marks": [
        (560, 212, 1500, 282, None)]},
    "u4_texto_columnas_resultado": {"crop": (0, 190, 1500, 900), "marks": []},
}

# Menu bar positions (raw px) used to highlight "where to click".
MENU_BOXES = {
    "Archivo": (2, 0, 128, 54), "Editar": (146, 0, 244, 54),
    "Ver": (258, 0, 324, 54), "Insertar": (340, 0, 466, 54),
    "Formato": (482, 0, 614, 54), "Estilos": (630, 0, 740, 54),
    "Hoja": (756, 0, 836, 54), "Datos": (852, 0, 950, 54),
    "Herramientas": (966, 0, 1172, 54),
}


# ===========================================================================
# Phase 1: capture
# ===========================================================================
def capture(selected):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import lo_automation as lo
    from course_dataset import HEADERS, rows, MESSY_CLIENTS, CATEGORIES

    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(WORK_DIR, exist_ok=True)
    office = lo.Office(profile_dir=os.path.join(ROOT, "build", "lo-profile")).start()
    ctx = office.ctx
    smgr = ctx.ServiceManager

    def want(*names):
        return not selected or any(n in selected for n in names)

    def locale_es():
        loc = lo.uno.createUnoStruct("com.sun.star.lang.Locale")
        loc.Language, loc.Country = "es", "CO"
        return loc

    def std_format(doc, kind):
        # kind: com.sun.star.util.NumberFormat constant (DATE=2, CURRENCY=8)
        return doc.NumberFormats.getStandardFormat(kind, locale_es())

    def new_doc(name):
        doc = office.new_calc()
        path = os.path.join(WORK_DIR, name + ".ods")
        doc.storeAsURL(lo.url(path), lo.props(Overwrite=True))
        wid = lo.wait_window(name + ".ods")
        lo.place_window(wid, 0, 0, WIN_W, WIN_H)
        time.sleep(1.5)
        return doc, wid

    def in_edit_mode(path):
        """True if a stray keystroke put Calc in cell-edit mode (red X in formula bar)."""
        from PIL import Image
        with Image.open(path) as im:
            if im.width != WIN_W:
                return False
            box = im.convert("RGB").crop((380, 212, 620, 282))
            red = sum(1 for r, g, b in box.getdata() if r > 180 and g < 90 and b < 90)
            return red > 40

    def shot(wid, name, settle=1.0, doc=None):
        time.sleep(settle)
        path = os.path.join(RAW_DIR, name + ".png")
        for attempt in range(4):
            lo.grab(wid, path)
            if not in_edit_mode(path):
                break
            # Calc windows grab keyboard focus: if the user typed meanwhile,
            # cancel that input and shoot again.
            print(f"  ! {name}: stray keyboard input detected, retrying")
            if doc is not None:
                office.dispatch(doc, ".uno:Cancel")
            time.sleep(1.0)
        print(f"  captured {name}")

    def dialog_shot(doc, command, name, settle=1.5, **args):
        before = {w for w, _ in lo.list_windows()}
        office.dispatch_async(doc, command, **args)
        end = time.time() + 15
        wid = None
        while time.time() < end and not wid:
            for w, _t in lo.list_windows():
                if w not in before:
                    wid = w
                    break
            time.sleep(0.3)
        if not wid:
            print(f"  !! dialog for {command} did not appear")
            return
        shot(wid, name, settle)
        lo.close_window(wid)
        time.sleep(1.0)

    def select(doc, ref):
        sh = doc.CurrentController.ActiveSheet
        doc.CurrentController.select(sh.getCellRangeByName(ref))

    def put_sales(doc, with_total=False, total_formula=True, fmt=True):
        sh = doc.Sheets.getByIndex(0)
        heads = HEADERS + (["Total"] if with_total else [])
        for c, h in enumerate(heads):
            sh.getCellByPosition(c, 0).setString(h)
        base = __import__("datetime").date(1899, 12, 30)
        for r, row in enumerate(rows(), start=1):
            d, client, product, cat, seller, qty, price = row
            sh.getCellByPosition(0, r).setValue((d - base).days)
            for c, v in enumerate([client, product, cat, seller], start=1):
                sh.getCellByPosition(c, r).setString(v)
            sh.getCellByPosition(5, r).setValue(qty)
            sh.getCellByPosition(6, r).setValue(price)
            if with_total:
                sh.getCellByPosition(7, r).setFormula(f"=F{r+1}*G{r+1}")
        n = len(rows()) + 1
        last = "H" if with_total else "G"
        if fmt:
            sh.getCellRangeByName(f"A2:A{n}").NumberFormat = std_format(doc, 2)
            sh.getCellRangeByName(f"G2:{last}{n}").NumberFormat = std_format(doc, 8)
            sh.getCellRangeByName(f"A1:{last}1").CharWeight = 150.0
            cols = sh.Columns
            for i in range(len(heads)):
                cols.getByIndex(i).OptimalWidth = True
        else:
            sh.getCellRangeByName(f"A2:A{n}").NumberFormat = std_format(doc, 2)
        return sh, n

    # ------------------------------------------------------------ Unit 0
    if want("u0_ventana_calc"):
        doc, wid = new_doc("mi_primera_hoja")
        # shorter window: the labelled parts stay, the empty grid shrinks
        lo.place_window(wid, 0, 0, WIN_W, 1060)
        select(doc, "A1")
        shot(wid, "u0_ventana_calc", 2.0, doc=doc)
        doc.close(True)

    # ------------------------------------------------------------ Unit 1
    if want("u1_celda_activa"):
        doc, wid = new_doc("ventas_la_universal")
        select(doc, "C3")
        shot(wid, "u1_celda_activa", doc=doc)
        doc.close(True)

    if want("u1_datos_crudos", "u1_formato_celdas", "u1_datos_formateados",
            "u1_autoformato", "u1_tabla_estilo"):
        doc, wid = new_doc("ventas_la_universal")
        sh, n = put_sales(doc, fmt=False)
        select(doc, "G2")
        shot(wid, "u1_datos_crudos", doc=doc)
        # currency applied, then open Formato de celdas so "Moneda" is shown
        sh.getCellRangeByName(f"G2:G{n}").NumberFormat = std_format(doc, 8)
        select(doc, f"G2:G{n}")
        dialog_shot(doc, ".uno:FormatCellDialog", "u1_formato_celdas")
        sh.getCellRangeByName("A1:G1").CharWeight = 150.0
        for i in range(7):
            sh.Columns.getByIndex(i).OptimalWidth = True
        select(doc, "A1")
        shot(wid, "u1_datos_formateados", doc=doc)
        select(doc, f"A1:G{n}")
        dialog_shot(doc, ".uno:AutoFormat", "u1_autoformato")
        fmts = smgr.createInstanceWithContext("com.sun.star.sheet.TableAutoFormats", ctx)
        names = list(fmts.ElementNames)
        print("  autoformats:", names)
        pick = next((x for x in names if "Azul" in x or "Blue" in x), names[0])
        sh.getCellRangeByName(f"A1:G{n}").autoFormat(pick)
        # AutoFormat also resets number formats: put dates and money back
        sh.getCellRangeByName(f"A2:A{n}").NumberFormat = std_format(doc, 2)
        sh.getCellRangeByName(f"G2:G{n}").NumberFormat = std_format(doc, 8)
        for i in range(7):
            sh.Columns.getByIndex(i).OptimalWidth = True
        doc.CurrentController.freezeAtPosition(0, 1)
        select(doc, "B2")
        shot(wid, "u1_tabla_estilo", doc=doc)
        doc.close(True)

    # ------------------------------------------------------------ Unit 2
    if want("u2_formula_simple", "u2_autosuma"):
        doc, wid = new_doc("calculos_rapidos")
        sh = doc.Sheets.getByIndex(0)
        sh.getCellRangeByName("A1").setString("Sin igual")
        sh.getCellRangeByName("B1").setString("4*35000")
        sh.getCellRangeByName("A2").setString("Con igual")
        sh.getCellRangeByName("B2").setFormula("=4*35000")
        sh.getCellRangeByName("A1:A2").CharWeight = 150.0
        sh.Columns.getByIndex(1).Width = 3500
        select(doc, "B2")
        shot(wid, "u2_formula_simple", doc=doc)
        select(doc, "B3")
        shot(wid, "u2_autosuma", doc=doc)
        doc.close(True)

    if want("u2_formula_referencias", "u2_copiar_formula", "u2_funciones",
            "u2_filtro", "u2_error_nombre"):
        doc, wid = new_doc("ventas_la_universal")
        sh, n = put_sales(doc, with_total=True)
        sh.getCellRangeByName("H1").CharWeight = 150.0
        sh.Columns.getByIndex(7).OptimalWidth = True
        select(doc, "H2")
        shot(wid, "u2_formula_referencias", doc=doc)
        select(doc, f"H2:H{n}")
        shot(wid, "u2_copiar_formula", doc=doc)
        labels = [("Total vendido", f"=SUM(H2:H{n})"),
                  ("Venta promedio", f"=AVERAGE(H2:H{n})"),
                  ("Venta más alta", f"=MAX(H2:H{n})"),
                  ("Venta más baja", f"=MIN(H2:H{n})"),
                  ("Número de ventas", f"=COUNT(H2:H{n})")]
        # summary block placed to the right, on the visible area
        sh.getCellRangeByName("J1").setString("Resumen del período")
        sh.getCellRangeByName("J1").CharWeight = 150.0
        for i, (lab, f) in enumerate(labels, start=2):
            sh.getCellByPosition(9, i - 1).setString(lab)
            c = sh.getCellByPosition(10, i - 1)
            c.setFormula(f)
            c.NumberFormat = std_format(doc, 8) if i < 6 else 0
        sh.Columns.getByIndex(9).OptimalWidth = True
        sh.Columns.getByIndex(10).OptimalWidth = True
        # hide some middle columns so the summary is visible next to totals
        for col in (1, 4):
            sh.Columns.getByIndex(col).IsVisible = False
        select(doc, "K2")
        shot(wid, "u2_funciones", doc=doc)
        for col in (1, 4):
            sh.Columns.getByIndex(col).IsVisible = True
        sh.getCellRangeByName("J1:K6").clearContents(1 | 2 | 4 | 16)
        # a typo on purpose
        sh.getCellRangeByName(f"J2").setString("Total vendido")
        sh.getCellRangeByName(f"K2").setFormula(f"=SUMMA(H2:H{n})")
        for col in (1, 2, 4):
            sh.Columns.getByIndex(col).IsVisible = False
        select(doc, "K2")
        shot(wid, "u2_error_nombre", doc=doc)
        for col in (1, 2, 4):
            sh.Columns.getByIndex(col).IsVisible = True
        sh.getCellRangeByName("J2:K2").clearContents(1 | 2 | 4 | 16)
        # AutoFilter on a named database range, filtered by Categoría = Pinturas
        addr = sh.getCellRangeByName(f"A1:H{n}").RangeAddress
        doc.DatabaseRanges.addNewByName("Ventas", addr)
        dbr = doc.DatabaseRanges.getByName("Ventas")
        dbr.AutoFilter = True
        fd = dbr.getFilterDescriptor()
        field = lo.uno.createUnoStruct("com.sun.star.sheet.TableFilterField")
        field.Field = 3
        field.Operator = lo.uno.Enum("com.sun.star.sheet.FilterOperator", "EQUAL")
        field.IsNumeric = False
        field.StringValue = "Pinturas"
        fd.setFilterFields((field,))
        dbr.refresh()
        select(doc, "A1")
        shot(wid, "u2_filtro", doc=doc)
        doc.close(True)

    # ------------------------------------------------------------ Unit 3
    if want("u3_ordenar_dialogo", "u3_ordenado", "u3_subtotales_dialogo",
            "u3_subtotales_resultado", "u3_subtotales_nivel2"):
        doc, wid = new_doc("ventas_la_universal")
        sh, n = put_sales(doc, with_total=True)
        sh.getCellRangeByName("H1").CharWeight = 150.0
        sh.Columns.getByIndex(7).OptimalWidth = True
        select(doc, "D2")
        dialog_shot(doc, ".uno:DataSort", "u3_ordenar_dialogo")
        rng = sh.getCellRangeByName(f"A1:H{n}")
        sf = lo.uno.createUnoStruct("com.sun.star.table.TableSortField")
        sf.Field, sf.IsAscending = 3, True
        sort_desc = rng.createSortDescriptor()
        for p in sort_desc:
            if p.Name == "SortFields":
                p.Value = lo.uno.Any("[]com.sun.star.table.TableSortField", (sf,))
            elif p.Name == "ContainsHeader":
                p.Value = True
        lo.uno.invoke(rng, "sort", (sort_desc,))
        select(doc, "D2")
        shot(wid, "u3_ordenado", doc=doc)
        sub = rng.createSubTotalDescriptor(True)
        col = lo.uno.createUnoStruct("com.sun.star.sheet.SubTotalColumn")
        col.Column = 7
        col.Function = lo.uno.Enum("com.sun.star.sheet.GeneralFunction", "SUM")
        sub.addNew((col,), 3)
        rng.applySubTotals(sub, True)
        select(doc, "D2")
        dialog_shot(doc, ".uno:DataSubTotals", "u3_subtotales_dialogo")
        select(doc, "A1")
        shot(wid, "u3_subtotales_resultado", doc=doc)
        rows_enum = lo.uno.Enum("com.sun.star.table.TableOrientation", "ROWS")
        sh.showLevel(1, rows_enum)  # API levels are 0-based: 1 == outline button "2"
        select(doc, "A1")
        shot(wid, "u3_subtotales_nivel2", doc=doc)
        doc.close(True)

    if want("u3_sumar_si", "u3_grafico_asistente", "u3_grafico_columnas",
            "u3_grafico_circular"):
        doc, wid = new_doc("resumen_la_universal")
        sh = doc.Sheets.getByIndex(0)
        sh.Name = "Resumen"
        data = doc.Sheets
        data.insertNewByName("Ventas", 1)
        vs = data.getByName("Ventas")
        base = __import__("datetime").date(1899, 12, 30)
        for c, h in enumerate(HEADERS + ["Total"]):
            vs.getCellByPosition(c, 0).setString(h)
        for r, row in enumerate(rows(with_total=True), start=1):
            vs.getCellByPosition(0, r).setValue((row[0] - base).days)
            for c in range(1, 5):
                vs.getCellByPosition(c, r).setString(row[c])
            for c in range(5, 8):
                vs.getCellByPosition(c, r).setValue(row[c])
        n = len(rows()) + 1
        sh.getCellRangeByName("A1").setString("Categoría")
        sh.getCellRangeByName("B1").setString("Total vendido")
        sh.getCellRangeByName("A1:B1").CharWeight = 150.0
        for i, cat in enumerate(CATEGORIES, start=2):
            sh.getCellByPosition(0, i - 1).setString(cat)
            sh.getCellByPosition(1, i - 1).setFormula(
                f'=SUMIF($Ventas.$D$2:$D${n};A{i};$Ventas.$H$2:$H${n})')
        last = len(CATEGORIES) + 1
        sh.getCellRangeByName(f"B2:B{last}").NumberFormat = std_format(doc, 8)
        sh.Columns.getByIndex(0).OptimalWidth = True
        sh.Columns.getByIndex(1).OptimalWidth = True
        select(doc, "B2")
        shot(wid, "u3_sumar_si", doc=doc)
        select(doc, f"A1:B{last}")
        dialog_shot(doc, ".uno:InsertObjectChart", "u3_grafico_asistente", settle=2.5)
        # real embedded charts
        rect = lo.uno.createUnoStruct("com.sun.star.awt.Rectangle")
        rect.X, rect.Y, rect.Width, rect.Height = 6500, 300, 14000, 8500
        addr = sh.getCellRangeByName(f"A1:B{last}").RangeAddress
        sh.Charts.addNewByName("Ventas", rect, (addr,), True, True)
        chart = sh.Charts.getByName("Ventas").EmbeddedObject
        chart.HasMainTitle = True
        chart.Title.String = "Ventas por categoría (septiembre)"
        chart.HasLegend = False
        select(doc, "A1")
        shot(wid, "u3_grafico_columnas", 2.0, doc=doc)
        chart.setDiagram(chart.createInstance("com.sun.star.chart.PieDiagram"))
        chart.HasLegend = True
        chart.Diagram.DataCaption = 4  # percentage labels
        shot(wid, "u3_grafico_circular", 2.0, doc=doc)
        doc.close(True)

    # ------------------------------------------------------------ Unit 4
    if want("u4_datos_sucios", "u4_espacios", "u4_nompropio",
            "u4_pegado_especial", "u4_texto_columnas_dialogo",
            "u4_texto_columnas_resultado", "u4_duplicados_dialogo",
            "u4_validez_dialogo"):
        doc, wid = new_doc("clientes_sucios")
        sh = doc.Sheets.getByIndex(0)
        for c, h in enumerate(["Cliente (como llegó)", "Categoría"]):
            sh.getCellByPosition(c, 0).setString(h)
        for r, (client, cat) in enumerate(MESSY_CLIENTS, start=1):
            sh.getCellByPosition(0, r).setString(client)
            sh.getCellByPosition(1, r).setString(cat)
        m = len(MESSY_CLIENTS) + 1
        sh.getCellRangeByName("A1:D1").CharWeight = 150.0
        sh.Columns.getByIndex(0).Width = 5200
        sh.Columns.getByIndex(1).Width = 3600
        select(doc, "A2")
        shot(wid, "u4_datos_sucios", doc=doc)
        sh.getCellRangeByName("C1").setString("Sin espacios")
        for r in range(2, m + 1):
            sh.getCellByPosition(2, r - 1).setFormula(f"=TRIM(A{r})")
        sh.Columns.getByIndex(2).Width = 4400
        select(doc, "C2")
        shot(wid, "u4_espacios", doc=doc)
        sh.getCellRangeByName("D1").setString("Nombre limpio")
        for r in range(2, m + 1):
            sh.getCellByPosition(3, r - 1).setFormula(f"=PROPER(TRIM(A{r}))")
        sh.Columns.getByIndex(3).Width = 4400
        select(doc, "D2")
        shot(wid, "u4_nompropio", doc=doc)
        # Text to columns on a clean name column
        sh.getCellRangeByName("A1:D20").clearContents(1 | 2 | 4 | 16 | 256)
        names = ["Pedro Pérez", "Ana Gómez", "Carlos Ruiz", "Marta Díaz",
                 "Jorge León", "Luisa Mora"]
        sh.getCellRangeByName("A1").setString("Nombre completo")
        sh.getCellRangeByName("B1").setString("Apellido")
        for r, nm in enumerate(names, start=1):
            sh.getCellByPosition(0, r).setString(nm)
        select(doc, f"A2:A{len(names)+1}")
        dialog_shot(doc, ".uno:TextToColumns", "u4_texto_columnas_dialogo", settle=2.0)
        sh.getCellRangeByName("A1").setString("Nombre")
        for r, nm in enumerate(names, start=1):
            first, last_name = nm.split(" ", 1)
            sh.getCellByPosition(0, r).setString(first)
            sh.getCellByPosition(1, r).setString(last_name)
        select(doc, "A1")
        shot(wid, "u4_texto_columnas_resultado", doc=doc)
        # Duplicates: repeated clients
        sh.getCellRangeByName("A1:D20").clearContents(1 | 2 | 4 | 16 | 256)
        dup = ["Pedro Pérez", "Ana Gómez", "Pedro Pérez", "Carlos Ruiz",
               "Ana Gómez", "Marta Díaz"]
        sh.getCellRangeByName("A1").setString("Cliente")
        for r, nm in enumerate(dup, start=1):
            sh.getCellByPosition(0, r).setString(nm)
        select(doc, f"A1:A{len(dup)+1}")
        dialog_shot(doc, ".uno:HandleDuplicateRecords", "u4_duplicados_dialogo")
        # Validity: category list
        sh.getCellRangeByName("A1:D20").clearContents(1 | 2 | 4 | 16 | 256)
        sh.getCellRangeByName("A1").setString("Categoría")
        rng = sh.getCellRangeByName("A2:A30")
        v = rng.Validation
        v.Type = lo.uno.Enum("com.sun.star.sheet.ValidationType", "LIST")
        v.setFormula1(";".join(f'"{c}"' for c in CATEGORIES))
        v.ShowList = 1
        rng.Validation = v
        select(doc, "A2:A30")
        dialog_shot(doc, ".uno:Validation", "u4_validez_dialogo")
        # Paste special last: the copy marquee would show in later shots
        sh.getCellRangeByName("A1:D20").clearContents(1 | 2 | 4 | 16 | 256)
        for r, (client, _cat) in enumerate(MESSY_CLIENTS, start=1):
            sh.getCellByPosition(0, r).setString(client)
            sh.getCellByPosition(1, r).setFormula(f"=PROPER(TRIM(A{r+1}))")
        select(doc, f"B2:B{m}")
        office.dispatch(doc, ".uno:Copy")
        select(doc, "C2")
        dialog_shot(doc, ".uno:PasteSpecial", "u4_pegado_especial")
        doc.close(True)

    office.stop()


# ===========================================================================
# Phase 2: annotate
# ===========================================================================
ACCENT = (230, 81, 0)          # orange highlight, readable on light UI
BADGE_TEXT = (255, 255, 255)


def _font(size):
    from PIL import ImageFont
    for path in ("/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf",
                 "/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf",
                 "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                 "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


def annotate(selected):
    from PIL import Image, ImageDraw
    os.makedirs(OUT_DIR, exist_ok=True)
    names = sorted(f[:-4] for f in os.listdir(RAW_DIR) if f.endswith(".png"))
    for name in names:
        if selected and name not in selected:
            continue
        img = Image.open(os.path.join(RAW_DIR, name + ".png")).convert("RGB")
        spec = ANNOTATIONS.get(name, {})
        marks = list(spec.get("marks", []))
        for menu in spec.get("menus", []):
            marks.append(MENU_BOXES[menu] + (None,))
        draw = ImageDraw.Draw(img)
        font = _font(34)
        for mark in marks:
            x0, y0, x1, y1, label = mark[:5]
            badge_at = mark[5] if len(mark) > 5 else None
            draw.rounded_rectangle((x0 + 2, y0 + 2, x1 - 2, y1 - 2), radius=10,
                                   outline=ACCENT, width=6)
            if label:
                r = 26
                cx = min(max(x0 + r + 4, r + 4), img.width - r - 4)
                cy = y0 + r + 4 if y0 > 60 or x0 > 60 else y1 - r - 4
                cx, cy = (x1 - r - 8, (y0 + y1) // 2) if (x1 - x0) > 3 * (y1 - y0) \
                    else (cx, cy)
                if badge_at:
                    cx, cy = badge_at
                draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ACCENT,
                             outline=(255, 255, 255), width=4)
                draw.text((cx, cy), label, fill=BADGE_TEXT, font=font, anchor="mm")
        crop = spec.get("crop")
        if crop:
            img = img.crop((crop[0], crop[1], min(crop[2], img.width),
                            min(crop[3], img.height)))
        out = os.path.join(OUT_DIR, name + ".png")
        img.save(out, optimize=True)
        print(f"  annotated {name} -> {img.width}x{img.height}")


if __name__ == "__main__":
    args = sys.argv[1:]
    phase = args[0] if args and args[0] in ("capture", "annotate") else "all"
    selected = set(args[1:] if phase != "all" else args)
    if phase in ("all", "capture"):
        capture(selected)
    if phase in ("all", "annotate"):
        annotate(selected)
