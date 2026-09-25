"""Sample data for "Ferretería La Universal" (Spanish, as shown to learners).

Shared by capture_screenshots.py and make_practice_files.py so that the
screenshots and the downloadable practice files always show the same data.
"""

import datetime as dt

HEADERS = ["Fecha", "Cliente", "Producto", "Categoría", "Vendedor",
           "Cantidad", "Precio unitario"]

# (day of September 2026, client, product, category, seller, qty, unit price COP)
SALES = [
    (1, "Pedro Pérez", "Cemento gris 50 kg", "Construcción", "Juan", 4, 35000),
    (1, "Ana Gómez", "Tornillos drywall x100", "Tornillería", "Luz", 2, 12000),
    (1, "Carlos Ruiz", "Pintura blanca galón", "Pinturas", "Juan", 1, 68000),
    (2, "Marta Díaz", "Brocha 3 pulgadas", "Pinturas", "Luz", 3, 9500),
    (2, "Pedro Pérez", "Varilla corrugada 1/2", "Construcción", "Juan", 10, 18500),
    (2, "Jorge León", "Martillo de uña", "Herramientas", "Andrés", 1, 32000),
    (3, "Ana Gómez", "Cinta aislante", "Eléctricos", "Luz", 5, 4500),
    (3, "Luisa Mora", "Bombillo LED 12 W", "Eléctricos", "Andrés", 6, 8900),
    (3, "Carlos Ruiz", "Rodillo antigota", "Pinturas", "Juan", 2, 21000),
    (4, "Jorge León", "Tubo PVC 1/2 x 3 m", "Plomería", "Andrés", 8, 7800),
    (4, "Marta Díaz", "Llave de paso", "Plomería", "Luz", 2, 26500),
    (4, "Pedro Pérez", "Arena lavada bulto", "Construcción", "Juan", 6, 9000),
    (5, "Luisa Mora", "Destornillador pala", "Herramientas", "Andrés", 2, 11500),
    (5, "Ana Gómez", "Chazos plásticos x50", "Tornillería", "Luz", 3, 6000),
    (5, "Carlos Ruiz", "Pintura azul cuarto", "Pinturas", "Juan", 2, 29000),
    (7, "Jorge León", "Cable eléctrico 12 AWG m", "Eléctricos", "Andrés", 20, 3200),
    (7, "Marta Díaz", "Pegante PVC", "Plomería", "Luz", 1, 14500),
    (7, "Pedro Pérez", "Cemento gris 50 kg", "Construcción", "Juan", 5, 35000),
    (8, "Luisa Mora", "Flexómetro 5 m", "Herramientas", "Andrés", 1, 18000),
    (8, "Ana Gómez", "Tuercas 3/8 x20", "Tornillería", "Luz", 4, 5500),
    (8, "Carlos Ruiz", "Thinner galón", "Pinturas", "Juan", 1, 42000),
    (9, "Jorge León", "Tomacorriente doble", "Eléctricos", "Andrés", 3, 9800),
    (9, "Marta Díaz", "Sifón lavaplatos", "Plomería", "Luz", 1, 23000),
    (9, "Pedro Pérez", "Bloque #5", "Construcción", "Juan", 50, 1900),
]


def sale_date(day):
    return dt.date(2026, 9, day)


def rows(with_total=False):
    """Sales as plain Python rows (dates as datetime.date)."""
    out = []
    for day, client, product, cat, seller, qty, price in SALES:
        row = [sale_date(day), client, product, cat, seller, qty, price]
        if with_total:
            row.append(qty * price)
        out.append(row)
    return out


# Messy copy used in Unit 4 (data cleaning). Same people, typed badly.
MESSY_CLIENTS = [
    ("  pedro PÉREZ ", "Construcción"),
    ("ANA gómez", "tornillería"),
    ("carlos   ruiz", "Pinturas "),
    ("Marta díaz  ", "PINTURAS"),
    (" pedro pérez", "construccion"),
    ("jorge LEÓN", "Herramientas"),
    ("ana GÓMEZ ", "Eléctricos"),
    ("LUISA mora", "eléctricos"),
    ("Carlos Ruiz", "Pinturas"),
    ("jorge león  ", "Plomería"),
]

CATEGORIES = ["Construcción", "Eléctricos", "Herramientas", "Pinturas",
              "Plomería", "Tornillería"]
