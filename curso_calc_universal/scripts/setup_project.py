import os
import sys
import shutil

def create_or_update_file(filepath, content):
    """Crea o actualiza un archivo, escribiendo solo si hay cambios reales."""
    exists = os.path.exists(filepath)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    if exists:
        with open(filepath, 'r', encoding='utf-8') as f:
            if f.read() == content:
                print(f"⚡ Sin cambios: {filepath}")
                return
                
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
    action = "🔄 Actualizado" if exists else "✅ Creado"
    print(f"{action}: {filepath}")

def main():
    print("Iniciando orquestador del proyecto 'Curso Calc Universal'...\n")
    
    # Detectar inteligentemente si el script se corre desde /scripts o desde afuera
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) == "scripts":
        base_dir = os.path.dirname(current_dir) # El proyecto es la carpeta padre
    else:
        base_dir = os.path.join(current_dir, "curso_calc_universal")

    os.makedirs(base_dir, exist_ok=True)
    
    # =====================================================================
    # 1. ARCHIVO HTML PRINCIPAL (AHORA CON TODAS LAS UNIDADES)
    # =====================================================================
    html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Curso Calc - Ferretería La Universal</title>
    <script src="https://cdn.tailwindcss.com?plugins=typography"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #f3f4f6; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #f1f1f1; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
    </style>
</head>
<body class="h-screen w-screen overflow-hidden flex text-gray-800">

    <aside class="w-80 bg-slate-900 text-white flex flex-col shadow-2xl z-20 hidden md:flex h-full">
        <div class="p-6 bg-slate-950 border-b border-slate-800">
            <div class="flex items-center gap-3">
                <i class="fas fa-tools text-3xl text-amber-500"></i>
                <div>
                    <h1 class="text-xl font-bold leading-tight">La Universal</h1>
                    <p class="text-xs text-slate-400 font-semibold uppercase tracking-wider">Escuela de Datos</p>
                </div>
            </div>
        </div>
        <div class="p-6 flex-1 overflow-y-auto">
            <p class="text-xs text-slate-400 font-semibold mb-4 uppercase tracking-wider">Contenido del Curso</p>
            <ul id="unit-list" class="space-y-2"></ul>
        </div>
    </aside>

    <main class="flex-1 flex flex-col h-full bg-slate-50 relative">
        <header class="md:hidden bg-slate-900 text-white p-4 flex justify-between items-center shadow-md z-20">
            <div class="flex items-center gap-2">
                <i class="fas fa-tools text-amber-500"></i><h1 class="font-bold">La Universal</h1>
            </div>
            <button id="mobile-menu-btn" class="p-2 bg-slate-800 rounded"><i class="fas fa-bars"></i></button>
        </header>

        <div id="mobile-menu" class="hidden absolute top-14 left-0 w-full bg-slate-900 z-30 max-h-[80vh] overflow-y-auto">
            <ul id="mobile-unit-list" class="p-4 space-y-2"></ul>
        </div>

        <div class="flex-1 overflow-y-auto p-4 md:p-8 relative w-full flex justify-center">
            <div class="max-w-5xl w-full h-full flex flex-col">
                <div class="mb-6">
                    <span id="current-unit-badge" class="bg-blue-100 text-blue-800 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide"></span>
                    <h2 id="current-unit-title" class="text-3xl font-extrabold text-slate-800 mt-2">Cargando...</h2>
                </div>

                <div class="bg-white rounded-2xl shadow-sm border border-slate-200 flex-1 flex flex-col overflow-hidden">
                    <div id="slide-visual" class="h-64 md:h-96 bg-slate-100 border-b border-slate-200 flex items-center justify-center p-6 overflow-hidden relative"></div>
                    <div class="p-6 md:p-10 flex-1 overflow-y-auto">
                        <h3 id="slide-title" class="text-2xl font-bold text-slate-800 mb-4 border-b border-slate-100 pb-4"></h3>
                        <div id="slide-content" class="text-slate-600 prose prose-slate max-w-none text-lg"></div>
                    </div>
                    <div class="bg-slate-50 p-4 md:p-6 border-t border-slate-200 flex justify-between items-center">
                        <button id="btn-prev" class="flex items-center gap-2 px-4 py-2 bg-white border border-slate-300 rounded-lg shadow-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"><i class="fas fa-arrow-left"></i> Anterior</button>
                        <div class="text-sm font-semibold text-slate-500"><span id="slide-counter"></span></div>
                        <button id="btn-next" class="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg shadow-md hover:bg-blue-700">Siguiente <i class="fas fa-arrow-right"></i></button>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        const courseData = [
            {
                id: 1, unitName: "Unidad 1", title: "De la libreta al computador", icon: "fa-book",
                slides: [
                    {
                        title: 'El desafío de "La Universal"',
                        visual: `<img src="multimedia/img/image_a8cad46.jpg" class="max-w-full max-h-full object-contain shadow-lg">`,
                        text: `<p>Don Manolo y su equipo llevan el registro en un cuaderno de papel.</p><ul class="list-disc pl-5 mt-4"><li>Nadie entiende la letra.</li><li>Cuadrar la caja toma horas.</li></ul>`
                    },
                    {
                        title: 'Conoce a tu nuevo mejor empleado',
                        visual: `<img src="multimedia/img/image_b8d03d7.jpg" class="max-w-full max-h-full object-contain shadow-lg">`,
                        text: `<p>Calc es una "Hoja de Cálculo". Piensa en ella como un cuaderno gigante e inteligente.</p>`
                    },
                    {
                        title: 'Pasando la libreta a la pantalla',
                        visual: `<img src="multimedia/img/image_c8d03d8.jpg" class="max-w-full max-h-full object-contain shadow-lg">`,
                        text: `<p>En Calc cada tipo de información tiene su propia columna (Fecha, Cliente, Producto).</p>`
                    },
                    {
                        title: '¿Es plata, cantidad o fecha?',
                        visual: `<img src="multimedia/img/image_d8d03d9.jpg" class="max-w-full max-h-full object-contain shadow-lg">`,
                        text: `<p>Usa formatos para que "35000" se vea como "$ 35.000,00".</p>`
                    },
                    {
                        title: 'La magia de las Tablas',
                        visual: `<img src="multimedia/img/image_e8d03d0.jpg" class="max-w-full max-h-full object-contain shadow-lg">`,
                        text: `<p>No pintes celda por celda, usa "Formatear como tabla".</p>`
                    },
                    {
                        title: '¡Misión Cumplida!',
                        visual: `<img src="multimedia/img/image_f8d03d1.jpg" class="max-w-full max-h-full object-contain shadow-lg">`,
                        text: `<p>Hoy logramos que los datos estén limpios. ¡Listo para la Unidad 2!</p>`
                    }
                ]
            },
            {
                id: 2, unitName: "Unidad 2", title: "Que el computador calcule por mí", icon: "fa-calculator",
                slides: [
                    {
                        title: 'La regla de oro: El signo IGUAL (=)',
                        visual: `<div class="flex gap-8 w-full items-center bg-white p-6 rounded-xl shadow-md border"><div class="flex-1 text-center border-r pr-8"><p class="text-sm text-slate-500 mb-2 uppercase font-bold">Sin el igual</p><div class="bg-slate-100 p-3 rounded font-mono text-xl text-slate-700 font-bold border">10 * 5</div></div><div class="flex-1 text-center"><p class="text-sm text-green-600 mb-2 uppercase font-bold">Con el igual</p><div class="bg-green-100 p-3 rounded font-mono text-3xl text-green-700 font-bold border border-green-300 shadow-inner">= 50</div></div></div>`,
                        text: `<p>Calc necesita que le avises cuándo calcular. La llave mágica es el signo Igual (=).</p><ul class="list-disc pl-5"><li><strong>10*5</strong>: Calc lo deja como texto.</li><li><strong>=10*5</strong>: Calc muestra 50.</li></ul>`
                    },
                    {
                        title: 'El Top 5 de las Funciones',
                        visual: `<div class="grid grid-cols-2 gap-4 w-full"><div class="bg-blue-50 border p-3 rounded flex items-center gap-3"><div class="bg-blue-500 text-white rounded-full w-8 h-8 flex justify-center items-center font-bold">+</div><code class="text-blue-900 font-bold">=SUMA(A1:A10)</code></div><div class="bg-amber-50 border p-3 rounded flex items-center gap-3"><div class="bg-amber-500 text-white rounded-full w-8 h-8 flex justify-center items-center"><i class="fas fa-balance-scale"></i></div><code class="text-amber-900 font-bold">=PROMEDIO()</code></div><div class="bg-green-50 border p-3 rounded flex items-center gap-3"><div class="bg-green-500 text-white rounded-full w-8 h-8 flex justify-center items-center"><i class="fas fa-arrow-up"></i></div><code class="text-green-900 font-bold">=MAX()</code></div><div class="bg-red-50 border p-3 rounded flex items-center gap-3"><div class="bg-red-500 text-white rounded-full w-8 h-8 flex justify-center items-center"><i class="fas fa-arrow-down"></i></div><code class="text-red-900 font-bold">=MIN()</code></div></div>`,
                        text: `<p>Calc trae "recetas" matemáticas listas:</p><ul class="list-disc pl-5"><li><code>=SUMA()</code>: Toda la plata que entró hoy.</li><li><code>=PROMEDIO()</code>: Venta promedio.</li><li><code>=MAX() / =MIN()</code>: Venta más cara/barata.</li></ul>`
                    },
                    {
                        title: 'Filtrar no es borrar, es esconder',
                        visual: `<div class="w-full max-w-sm"><div class="w-full bg-slate-800 text-white rounded-t p-2 flex justify-between"><span class="font-bold text-sm">Datos</span><i class="fas fa-filter text-amber-400"></i></div><div class="w-full bg-white border rounded-b shadow"><div class="bg-slate-100 border-b grid grid-cols-2 font-bold text-sm p-2"><div class="border-r">Producto <i class="fas fa-caret-down text-blue-500"></i></div><div>Vendedor</div></div><div class="grid grid-cols-2 text-sm bg-amber-50 p-2"><div class="font-semibold text-amber-800">Cemento</div><div>Pedro</div></div></div></div>`,
                        text: `<p>Ve al menú <strong>Datos > Autofiltro</strong>. Te permite ocultar las filas que no te interesan temporalmente.</p>`
                    }
                ]
            },
            {
                id: 3, unitName: "Unidad 3", title: "Subtotales y Gráficos", icon: "fa-chart-pie",
                slides: [
                    {
                        title: 'El paso obligatorio (ORDENAR)',
                        visual: `<div class="flex flex-col items-center bg-white p-4 rounded shadow border max-w-sm"><div class="bg-amber-100 text-amber-800 font-bold px-3 py-1 rounded mb-4"><i class="fas fa-sort-alpha-down"></i> Botón A-Z</div><div class="w-full text-sm"><div class="p-2 border-b bg-blue-50 text-blue-800 font-semibold border-l-4 border-blue-500">Pintura</div><div class="p-2 border-b bg-blue-50 text-blue-800 font-semibold border-l-4 border-blue-500">Pintura</div><div class="p-2 bg-green-50 text-green-800 font-semibold border-l-4 border-green-500">Tornillería</div></div></div>`,
                        text: `<p>Antes de agrupar, ¡hay que ordenar! Calc necesita que todos los productos iguales estén juntos. Usa el botón <strong>A-Z</strong>.</p>`
                    },
                    {
                        title: 'El botón de Subtotales',
                        visual: `<div class="bg-white border rounded shadow-xl overflow-hidden max-w-md w-full"><div class="bg-blue-600 text-white p-2 text-sm font-bold flex justify-between"><span>Subtotales</span> <i class="fas fa-times"></i></div><div class="p-4 bg-slate-50 space-y-4 text-sm"><div><label class="block font-semibold">Agrupar por:</label><div class="border bg-white p-2 rounded">Categoría</div></div><div><label class="block font-semibold">Calcular para:</label><div class="border bg-white p-2 rounded"><i class="fas fa-check-square text-blue-600"></i> Valor</div></div></div></div>`,
                        text: `<p>Ve a <strong>Datos > Subtotales...</strong> Esto creará filas nuevas automáticas con la suma de cada categoría.</p>`
                    },
                    {
                        title: 'Pintando los datos (Gráficos)',
                        visual: `<div class="flex items-end gap-6 h-48 w-full max-w-md bg-white p-6 rounded shadow border"><div class="flex-1 h-full flex items-end justify-around border-b-2 border-l-2 pb-2 pl-2"><div class="w-12 bg-blue-500 rounded-t h-2/3"></div><div class="w-12 bg-green-500 rounded-t h-1/3"></div></div><div class="flex-1 flex justify-center items-center h-full"><i class="fas fa-chart-pie text-8xl text-amber-500"></i></div></div>`,
                        text: `<p>Selecciona tu resumen y ve a <strong>Insertar > Gráfico</strong>. Usa columnas para competir y circulares para ver proporciones.</p>`
                    }
                ]
            },
            {
                id: 4, unitName: "Unidad 4", title: "Limpiando el desastre", icon: "fa-broom",
                slides: [
                    {
                        title: 'El borrador de espacios',
                        visual: `<div class="flex flex-col gap-4 items-center w-full max-w-md"><div class="w-full bg-slate-200 p-3 rounded text-center font-mono border">"&nbsp;&nbsp;&nbsp;Pinturas&nbsp;&nbsp;&nbsp;Corona&nbsp;&nbsp;"</div><i class="fas fa-cut text-2xl text-blue-500"></i><div class="w-full bg-blue-100 p-3 rounded text-center font-mono font-bold text-blue-800 border">=RECORTAR(A1)</div><i class="fas fa-arrow-down text-xl"></i><div class="w-full bg-green-100 p-3 rounded text-center font-mono font-bold text-green-800 border">"Pinturas Corona"</div></div>`,
                        text: `<p>Nuestra primera escoba digital es <code>=RECORTAR()</code>. Quita todos los espacios sobrantes al inicio y al final.</p>`
                    },
                    {
                        title: 'Uniforme para el texto',
                        visual: `<div class="flex items-center gap-4 w-full max-w-md bg-white p-6 rounded shadow border"><div class="font-mono flex-1 text-center bg-slate-100 p-2 rounded">pInTuRas CORONA</div><div class="text-amber-500 text-2xl"><i class="fas fa-magic"></i></div><div class="font-bold text-blue-800 flex-1 text-center bg-blue-50 p-2 rounded border">Pinturas Corona</div></div>`,
                        text: `<p>Usa <code>=NOMPROPIO()</code> para que todo quede con la primera letra en mayúscula, muy elegante.</p>`
                    },
                    {
                        title: 'Divorciando celdas',
                        visual: `<div class="w-full max-w-md"><div class="flex items-center border rounded overflow-hidden mb-3"><div class="bg-slate-200 font-bold p-3 border-r">A1</div><div class="bg-white p-3 flex-1 font-semibold">Juan Perez</div></div><div class="flex gap-2"><div class="flex flex-1 items-center border border-blue-300 rounded"><div class="bg-blue-100 font-bold p-2 border-r text-xs">B1 (Nombre)</div><div class="bg-white p-2 flex-1 font-bold text-center">Juan</div></div><div class="flex flex-1 items-center border border-green-300 rounded"><div class="bg-green-100 font-bold p-2 border-r text-xs">C1 (Apellido)</div><div class="bg-white p-2 flex-1 font-bold text-center">Perez</div></div></div></div>`,
                        text: `<p>Para separar nombres y apellidos que están pegados, ve a <strong>Datos > Texto a columnas...</strong> y elige "Espacio".</p>`
                    }
                ]
            }
        ];

        let currentUnitIndex = 0; let currentSlideIndex = 0;
        
        function renderMenu() {
            const ul = document.getElementById('unit-list');
            const mul = document.getElementById('mobile-unit-list');
            ul.innerHTML = ''; mul.innerHTML = '';
            courseData.forEach((unit, idx) => {
                const btnHTML = `<button class="w-full text-left flex items-center gap-3 px-4 py-3 rounded-lg ${idx === currentUnitIndex ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800'}" onclick="goToUnit(${idx})"><i class="fas ${unit.icon}"></i> ${unit.unitName}</button>`;
                ul.innerHTML += `<li>${btnHTML}</li>`;
                mul.innerHTML += `<li>${btnHTML}</li>`;
            });
        }

        function goToUnit(idx) {
            currentUnitIndex = idx; currentSlideIndex = 0;
            document.getElementById('mobile-menu').classList.add('hidden');
            renderMenu(); renderSlide();
        }

        function renderSlide() {
            const unit = courseData[currentUnitIndex];
            const slide = unit.slides[currentSlideIndex];
            document.getElementById('current-unit-badge').textContent = unit.unitName;
            document.getElementById('current-unit-title').textContent = unit.title;
            document.getElementById('slide-visual').innerHTML = slide.visual;
            document.getElementById('slide-title').innerHTML = slide.title;
            document.getElementById('slide-content').innerHTML = slide.text;
            document.getElementById('slide-counter').textContent = `${currentSlideIndex + 1} / ${unit.slides.length}`;
            
            document.getElementById('btn-prev').disabled = (currentUnitIndex === 0 && currentSlideIndex === 0);
            
            const btnNext = document.getElementById('btn-next');
            if (currentUnitIndex === courseData.length - 1 && currentSlideIndex === unit.slides.length - 1) {
                btnNext.innerHTML = 'Finalizar <i class="fas fa-check"></i>';
                btnNext.className = "flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg shadow-md hover:bg-green-700";
            } else {
                btnNext.innerHTML = 'Siguiente <i class="fas fa-arrow-right"></i>';
                btnNext.className = "flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg shadow-md hover:bg-blue-700";
            }
        }

        document.getElementById('btn-next').addEventListener('click', () => {
            const unit = courseData[currentUnitIndex];
            if (currentSlideIndex < unit.slides.length - 1) { currentSlideIndex++; }
            else if (currentUnitIndex < courseData.length - 1) { currentUnitIndex++; currentSlideIndex = 0; renderMenu(); }
            renderSlide();
        });

        document.getElementById('btn-prev').addEventListener('click', () => {
            if (currentSlideIndex > 0) { currentSlideIndex--; }
            else if (currentUnitIndex > 0) { currentUnitIndex--; currentSlideIndex = courseData[currentUnitIndex].slides.length - 1; renderMenu(); }
            renderSlide();
        });

        document.getElementById('mobile-menu-btn').addEventListener('click', () => {
            document.getElementById('mobile-menu').classList.toggle('hidden');
        });

        renderMenu(); renderSlide();
    </script>
</body>
</html>"""

    # =====================================================================
    # 2. ARCHIVO IMSMANIFEST (Configurado para las imágenes de la U1)
    # =====================================================================
    manifest_content = """<?xml version="1.0" standalone="no" ?>
<manifest identifier="CalcPymesManifest" version="1.3" xmlns="http://www.imsglobal.org/xsd/imscp_v1p1">
    <metadata><schema>ADL SCORM</schema><schemaversion>2004 3rd Edition</schemaversion></metadata>
    <organizations default="default_org">
        <organization identifier="default_org">
            <title>Curso: Calc para Pymes (La Universal)</title>
            <item identifier="item_1" identifierref="resource_1"><title>Unidades del Curso</title></item>
        </organization>
    </organizations>
    <resources>
        <resource identifier="resource_1" type="webcontent" adlcp:scormtype="sco" href="curso_la_universal.html" xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_v1p3">
            <file href="curso_la_universal.html"/>
            <file href="multimedia/img/image_a8cad46.jpg"/>
            <file href="multimedia/img/image_b8d03d7.jpg"/>
            <file href="multimedia/img/image_c8d03d8.jpg"/>
            <file href="multimedia/img/image_d8d03d9.jpg"/>
            <file href="multimedia/img/image_e8d03d0.jpg"/>
            <file href="multimedia/img/image_f8d03d1.jpg"/>
        </resource>
    </resources>
</manifest>"""

    # =====================================================================
    # 3. SCRIPT PARA EMPAQUETAR SCORM EN LOCAL (¡NUEVO!)
    # =====================================================================
    pack_scorm_content = '''import os
import zipfile

def create_scorm_zip():
    # El script vive en scripts/, asi que la raiz es un nivel arriba
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_filename = os.path.join(base_dir, 'Curso_Calc_LaUniversal_SCORM.zip')
    
    print(f"\\nIniciando empaquetado SCORM en: {output_filename}\\n")
    
    # Archivos obligatorios a empaquetar
    files_to_zip = ['curso_la_universal.html', 'imsmanifest.xml']
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Añadir archivos base
        for file in files_to_zip:
            file_path = os.path.join(base_dir, file)
            if os.path.exists(file_path):
                zipf.write(file_path, file)
                print(f"  + Añadido: {file}")
            else:
                print(f"  ! FALTANTE: {file}")
        
        # Añadir toda la carpeta multimedia/
        media_dir = os.path.join(base_dir, 'multimedia')
        if os.path.exists(media_dir):
            for root, _, files in os.walk(media_dir):
                for file in files:
                    # Evitar añadir la carpeta de originales pesados al SCORM
                    if 'originales' not in root:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, base_dir)
                        zipf.write(file_path, arcname)
                        print(f"  + Añadido: {arcname}")
        else:
            print("  ! Carpeta 'multimedia' no encontrada.")
            
    print("\\n✅ EMPAQUETADO EXITOSO. Sube el archivo .zip a tu Moodle.\\n")

if __name__ == "__main__":
    create_scorm_zip()
'''

    # =====================================================================
    # 4. SCRIPT PARA OPTIMIZAR IMÁGENES (AHORA INCLUIDO EN EL ORQUESTADOR)
    # =====================================================================
    optimize_images_content = '''import os
import shutil
try:
    from PIL import Image
except ImportError:
    print("Error: La librería 'Pillow' no está instalada.")
    print("Por favor, ejecuta en tu terminal: pip install Pillow")
    exit()

def optimize_images(directory, max_width=1000, quality=80):
    print(f"\\nBuscando imágenes para optimizar en: {directory}\\n")

    if not os.path.exists(directory):
        print(f"❌ Error: No se encontró la carpeta '{directory}'.")
        return

    procesadas = 0
    ahorro_total_mb = 0

    originals_dir = os.path.join(directory, 'originales')
    os.makedirs(originals_dir, exist_ok=True)
    print(f"📁 Carpeta de respaldos lista en: {originals_dir}\\n")

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        if os.path.isfile(filepath) and filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            backup_path = os.path.join(originals_dir, filename)
            
            if not os.path.exists(backup_path):
                shutil.copy2(filepath, backup_path)
                print(f"  📥 Respaldo guardado: {filename}")
            
            source_filepath = backup_path
            original_size_bytes = os.path.getsize(source_filepath)

            try:
                img = Image.open(source_filepath)
                
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                if img.width > max_width:
                    wpercent = (max_width / float(img.width))
                    hsize = int((float(img.height) * float(wpercent)))
                    try:
                        resample_filter = Image.Resampling.LANCZOS
                    except AttributeError:
                        resample_filter = Image.LANCZOS
                    img = img.resize((max_width, hsize), resample_filter)
                    print(f"  📏 {filename}: Redimensionada a {max_width}x{hsize}px")

                img.save(filepath, "JPEG", optimize=True, quality=quality)
                
                new_size_bytes = os.path.getsize(filepath)
                ahorro_mb = (original_size_bytes - new_size_bytes) / (1024 * 1024)
                
                if ahorro_mb > 0:
                    ahorro_total_mb += ahorro_mb
                    
                procesadas += 1
                print(f"  ✅ {filename} optimizada.")

            except Exception as e:
                print(f"  ❌ Error al procesar {filename}: {e}")

    print("\\n" + "="*40)
    print(f"🎉 Proceso finalizado con éxito.")
    print(f"📸 Imágenes procesadas: {procesadas}")
    print(f"💾 Espacio ahorrado: {ahorro_total_mb:.2f} MB")
    print("="*40 + "\\n")

if __name__ == '__main__':
    # El script vive en scripts/, asi que buscamos la base un nivel arriba
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_directory = os.path.join(base_dir, 'multimedia', 'img')
    optimize_images(target_directory)
'''

    # =====================================================================
    # CREACIÓN FÍSICA DE ARCHIVOS Y CARPETAS
    # =====================================================================
    create_or_update_file(os.path.join(base_dir, "curso_la_universal.html"), html_content)
    create_or_update_file(os.path.join(base_dir, "imsmanifest.xml"), manifest_content)
    
    # Crear scripts utilitarios en la carpeta scripts
    create_or_update_file(os.path.join(base_dir, "scripts", "empaquetar_scorm.py"), pack_scorm_content)
    create_or_update_file(os.path.join(base_dir, "scripts", "optimize_images.py"), optimize_images_content)
    
    # Asegurar carpeta de imagenes
    img_dir = os.path.join(base_dir, "multimedia", "img")
    os.makedirs(img_dir, exist_ok=True)
    readme_path = os.path.join(img_dir, "README_IMG.txt")
    if not os.path.exists(readme_path):
        with open(readme_path, 'w') as f:
            f.write("Asegúrate de pegar aquí las imágenes .jpg")

    # Autoguardado: Mover una copia de este mismo script a la carpeta scripts/
    script_dest = os.path.join(base_dir, "scripts", "setup_project.py")
    if os.path.abspath(__file__) != os.path.abspath(script_dest):
        shutil.copy2(os.path.abspath(__file__), script_dest)
        print(f"📦 Utilidad orquestadora guardada en: {script_dest}")

    print("\n" + "="*50)
    print("🎉 PROYECTO ACTUALIZADO/CREADO EXITOSAMENTE 🎉")
    print("="*50)
    print(f"Directorio de trabajo: {base_dir}")
    print("NUEVAS INSTRUCCIONES DE PRUEBA:")
    print("1. Este orquestador ahora vive permanentemente en 'scripts/setup_project.py'.")
    print("2. Abre 'curso_la_universal.html' para ver TODAS las Unidades.")
    print("3. Para crear tu SCORM de Moodle, ve a la terminal en la raíz del proyecto y ejecuta:")
    print("   python scripts/empaquetar_scorm.py")
    print("4. Un archivo 'Curso_Calc_LaUniversal_SCORM.zip' aparecerá listo para Moodle.\n")

if __name__ == "__main__":
    main()
