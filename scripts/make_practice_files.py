"""Generate the downloadable practice workbooks (.ods) for each unit.

Runs LibreOffice headless through UNO, so no display is needed.
Output: curso_calc_universal/multimedia/practica/*.ods

    python3 scripts/make_practice_files.py
"""

import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lo_automation as lo  # noqa: E402
from course_dataset import (HEADERS, rows, MESSY_CLIENTS, CATEGORIES)  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "curso_calc_universal", "multimedia", "practica")
EPOCH = dt.date(1899, 12, 30)

BOLD = 150.0
HEADER_BG = 0xFDE7D3
TITLE_COLOR = 0xC24400


def std_format(doc, kind):
    loc = lo.uno.createUnoStruct("com.sun.star.lang.Locale")
    loc.Language, loc.Country = "es", "CO"
    return doc.NumberFormats.getStandardFormat(kind, loc)


def instructions(doc, title, steps, extra=None):
    """First sheet with the exercise in Spanish."""
    sh = doc.Sheets.getByIndex(0)
    sh.Name = "Instrucciones"
    sh.getCellRangeByName("A1").setString(title)
    a1 = sh.getCellRangeByName("A1")
    a1.CharWeight, a1.CharHeight, a1.CharColor = BOLD, 16.0, TITLE_COLOR
    sh.getCellRangeByName("A2").setString(
        "Curso LibreOffice Calc para pymes · Ferretería La Universal")
    sh.getCellRangeByName("A2").CharColor = 0x6B7486
    sh.getCellRangeByName("A4").setString("Pasos")
    sh.getCellRangeByName("A4").CharWeight = BOLD
    for i, step in enumerate(steps, start=5):
        sh.getCellByPosition(0, i - 1).setString(f"{i - 4}. {step}")
    row = len(steps) + 6
    for line in (extra or []):
        sh.getCellByPosition(0, row - 1).setString(line)
        sh.getCellByPosition(0, row - 1).CharColor = 0x245EA8
        row += 1
    sh.Columns.getByIndex(0).Width = 26000
    return sh


def sales_sheet(doc, name, with_total=None, formatted=True):
    """Sales table. with_total: None (no column), 'empty' or 'formula'."""
    doc.Sheets.insertNewByName(name, doc.Sheets.Count)
    sh = doc.Sheets.getByName(name)
    heads = HEADERS + (["Total"] if with_total else [])
    for c, h in enumerate(heads):
        sh.getCellByPosition(c, 0).setString(h)
    data = rows()
    for r, (d, client, product, cat, seller, qty, price) in enumerate(data, start=1):
        sh.getCellByPosition(0, r).setValue((d - EPOCH).days)
        for c, v in enumerate([client, product, cat, seller], start=1):
            sh.getCellByPosition(c, r).setString(v)
        sh.getCellByPosition(5, r).setValue(qty)
        sh.getCellByPosition(6, r).setValue(price)
        if with_total == "formula":
            sh.getCellByPosition(7, r).setFormula(f"=F{r + 1}*G{r + 1}")
    n = len(data) + 1
    last = "H" if with_total else "G"
    if formatted:
        head = sh.getCellRangeByName(f"A1:{last}1")
        head.CharWeight, head.CellBackColor = BOLD, HEADER_BG
        sh.getCellRangeByName(f"A2:A{n}").NumberFormat = std_format(doc, 2)
        sh.getCellRangeByName(f"G2:{last}{n}").NumberFormat = std_format(doc, 8)
        for i in range(len(heads)):
            sh.Columns.getByIndex(i).OptimalWidth = True
    return sh, n


def save(doc, filename):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, filename)
    # the file opens on the active sheet: make it the instructions
    doc.CurrentController.setActiveSheet(doc.Sheets.getByIndex(0))
    doc.storeToURL(lo.url(path), lo.props(FilterName="calc8", Overwrite=True))
    doc.close(True)
    print(f"  wrote {os.path.relpath(path, ROOT)}")


def main():
    office = lo.Office().start()
    try:
        # ---- Unit 1: format a raw table
        doc = office.new_calc(hidden=True)
        instructions(doc, "Práctica Unidad 1 · De la libreta al computador", [
            "Ve a la hoja «Ventas». Así quedaron las ventas recién pasadas de la libreta.",
            "Pon en negrita la fila 1 (encabezados): selecciónala y pulsa Ctrl+N.",
            "Ajusta la anchura de las columnas: Formato ▸ Columnas ▸ Anchura óptima…",
            "La columna A muestra números: aplícale Formato ▸ Formato numérico ▸ Fecha.",
            "Aplica formato de moneda a la columna G: Formato ▸ Formato de celdas… ▸ Números ▸ Moneda.",
            "Deja visibles los encabezados: Ver ▸ Inmovilizar celdas ▸ Inmovilizar primera fila.",
            "Opcional: selecciona la tabla y aplica Formato ▸ Estilos de formato automático… (revisa luego fechas y moneda).",
            "Guarda tu trabajo con Archivo ▸ Guardar como… y el nombre ventas_la_universal.ods.",
        ], ["Reto: agrega tres ventas nuevas del 10 de septiembre y aplícales el mismo formato."])
        sales_sheet(doc, "Ventas", formatted=False)
        save(doc, "practica_u1_libreta.ods")

        # ---- Unit 2: formulas and functions
        doc = office.new_calc(hidden=True)
        instructions(doc, "Práctica Unidad 2 · Que el computador calcule por mí", [
            "Ve a la hoja «Ventas». La columna H (Total) está vacía.",
            "En H2 escribe =F2*G2 y pulsa Intro.",
            "Copia la fórmula hasta la última venta: doble clic en el cuadrito de la esquina de H2.",
            "Completa el resumen de la columna K con SUMA, PROMEDIO, MAX, MIN y CONTAR sobre H2:H25.",
            "Activa Datos ▸ Filtro automático y muestra solo las ventas de «Juan» en la columna Vendedor.",
            "Mira la barra de estado: ¿cuánto vendió Juan? Luego vuelve a mostrar todo.",
        ], ["Recuerda: en español las funciones separan sus partes con punto y coma (;)."])
        sh, n = sales_sheet(doc, "Ventas", with_total="empty")
        labels = ["Total vendido", "Venta promedio", "Venta más alta", "Venta más baja", "Número de ventas"]
        sh.getCellRangeByName("J1").setString("Resumen del período")
        sh.getCellRangeByName("J1").CharWeight = BOLD
        for i, lab in enumerate(labels, start=2):
            sh.getCellByPosition(9, i - 1).setString(lab)
            sh.getCellByPosition(10, i - 1).CellBackColor = 0xFFF7E0
        sh.getCellRangeByName("K2:K5").NumberFormat = std_format(doc, 8)
        sh.getCellRangeByName(f"H2:H{n}").NumberFormat = std_format(doc, 8)
        sh.Columns.getByIndex(9).OptimalWidth = True
        sh.Columns.getByIndex(7).Width = 3200
        sh.Columns.getByIndex(10).Width = 3600
        save(doc, "practica_u2_formulas.ods")

        # ---- Unit 3: sort, subtotals, SUMIF, chart
        doc = office.new_calc(hidden=True)
        instructions(doc, "Práctica Unidad 3 · Ordenar, resumir y graficar", [
            "En la hoja «Ventas», ordena la tabla por Categoría: Datos ▸ Ordenar...",
            "Saca subtotales: Datos ▸ Subtotales... ▸ Agrupar por Categoría ▸ Total ▸ Suma.",
            "Usa los botones de esquema 1, 2 y 3 de la izquierda. ¿Qué categoría vendió más?",
            "Quita los subtotales: Datos ▸ Subtotales... ▸ Quitar.",
            "En la hoja «Resumen», escribe en B2: =SUMAR.SI($Ventas.$D$2:$D$25;A2;$Ventas.$H$2:$H$25)",
            "Copia la fórmula de B2 hasta B7 y aplica formato de moneda.",
            "Selecciona A1:B7 y crea un gráfico de columnas: Insertar ▸ Gráfico…",
        ], ["Reto: haz también un gráfico circular y compáralo con el de columnas."])
        sales_sheet(doc, "Ventas", with_total="formula")
        doc.Sheets.insertNewByName("Resumen", doc.Sheets.Count)
        rs = doc.Sheets.getByName("Resumen")
        rs.getCellRangeByName("A1").setString("Categoría")
        rs.getCellRangeByName("B1").setString("Total vendido")
        hd = rs.getCellRangeByName("A1:B1")
        hd.CharWeight, hd.CellBackColor = BOLD, HEADER_BG
        for i, cat in enumerate(CATEGORIES, start=2):
            rs.getCellByPosition(0, i - 1).setString(cat)
        rs.Columns.getByIndex(0).OptimalWidth = True
        rs.Columns.getByIndex(1).Width = 4000
        save(doc, "practica_u3_resumen.ods")

        # ---- Unit 4: cleaning
        doc = office.new_calc(hidden=True)
        instructions(doc, "Práctica Unidad 4 · Limpiando el desastre", [
            "Hoja «Clientes»: en C2 escribe =NOMPROPIO(ESPACIOS(A2)) y cópiala hacia abajo.",
            "Convierte la columna C en texto: cópiala y usa Editar ▸ Pegado especial… ▸ Solo valores.",
            "Arregla también las categorías de la columna B con =NOMPROPIO(ESPACIOS(B2)) en la columna D.",
            "Hoja «Nombres»: separa nombre y apellido con Datos ▸ Texto a columnas… (separador: espacio).",
            "Hoja «Duplicados»: encuentra los clientes repetidos con Datos ▸ Duplicados…",
            "Hoja «Categorías»: crea una lista desplegable en A2:A30 con Datos ▸ Validez… ▸ Permitir: Lista.",
        ], ["Ojo: nombres compuestos como «Luz Marina Rojas» quedan en tres columnas; revísalos a mano.",
            "Categorías permitidas: " + ", ".join(CATEGORIES) + "."])
        doc.Sheets.insertNewByName("Clientes", doc.Sheets.Count)
        cs = doc.Sheets.getByName("Clientes")
        for c, h in enumerate(["Cliente (como llegó)", "Categoría (como llegó)", "Cliente limpio", "Categoría limpia"]):
            cs.getCellByPosition(c, 0).setString(h)
        for r, (client, cat) in enumerate(MESSY_CLIENTS, start=1):
            cs.getCellByPosition(0, r).setString(client)
            cs.getCellByPosition(1, r).setString(cat)
        hd = cs.getCellRangeByName("A1:D1")
        hd.CharWeight, hd.CellBackColor = BOLD, HEADER_BG
        for i, w in enumerate([5600, 5200, 4800, 4800]):
            cs.Columns.getByIndex(i).Width = w

        doc.Sheets.insertNewByName("Nombres", doc.Sheets.Count)
        ns = doc.Sheets.getByName("Nombres")
        ns.getCellRangeByName("A1").setString("Nombre completo")
        ns.getCellRangeByName("B1").setString("Apellido")
        names = ["Pedro Pérez", "Ana Gómez", "Carlos Ruiz", "Marta Díaz", "Jorge León",
                 "Luisa Mora", "Luz Marina Rojas", "Andrés Castillo"]
        for r, nm in enumerate(names, start=1):
            ns.getCellByPosition(0, r).setString(nm)
        hd = ns.getCellRangeByName("A1:B1")
        hd.CharWeight, hd.CellBackColor = BOLD, HEADER_BG
        ns.Columns.getByIndex(0).Width = 5200
        ns.Columns.getByIndex(1).Width = 4200

        doc.Sheets.insertNewByName("Duplicados", doc.Sheets.Count)
        ds = doc.Sheets.getByName("Duplicados")
        ds.getCellRangeByName("A1").setString("Cliente")
        ds.getCellRangeByName("B1").setString("Teléfono")
        dup = [("Pedro Pérez", "310 555 0101"), ("Ana Gómez", "311 555 0102"),
               ("Pedro Pérez", "310 555 0101"), ("Carlos Ruiz", "312 555 0103"),
               ("Ana Gómez", "311 555 0102"), ("Marta Díaz", "313 555 0104"),
               ("Jorge León", "314 555 0105"), ("Carlos Ruiz", "312 555 0103")]
        for r, (nm, tel) in enumerate(dup, start=1):
            ds.getCellByPosition(0, r).setString(nm)
            ds.getCellByPosition(1, r).setString(tel)
        hd = ds.getCellRangeByName("A1:B1")
        hd.CharWeight, hd.CellBackColor = BOLD, HEADER_BG
        ds.Columns.getByIndex(0).Width = 4800
        ds.Columns.getByIndex(1).Width = 4000

        doc.Sheets.insertNewByName("Categorías", doc.Sheets.Count)
        ks = doc.Sheets.getByName("Categorías")
        ks.getCellRangeByName("A1").setString("Categoría")
        ks.getCellRangeByName("A1").CharWeight = BOLD
        ks.getCellRangeByName("A1").CellBackColor = HEADER_BG
        ks.Columns.getByIndex(0).Width = 5000
        save(doc, "practica_u4_limpieza.ods")
    finally:
        office.stop()


if __name__ == "__main__":
    main()
