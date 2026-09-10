import os
import shutil
try:
    from PIL import Image
except ImportError:
    print("Error: La librería 'Pillow' no está instalada.")
    print("Por favor, ejecuta en tu terminal: pip install Pillow")
    exit()

def optimize_images(directory, max_width=1000, quality=80):
    print(f"\nBuscando imágenes para optimizar en: {directory}\n")

    if not os.path.exists(directory):
        print(f"❌ Error: No se encontró la carpeta '{directory}'.")
        return

    procesadas = 0
    ahorro_total_mb = 0

    originals_dir = os.path.join(directory, 'originales')
    os.makedirs(originals_dir, exist_ok=True)
    print(f"📁 Carpeta de respaldos lista en: {originals_dir}\n")

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

    print("\n" + "="*40)
    print(f"🎉 Proceso finalizado con éxito.")
    print(f"📸 Imágenes procesadas: {procesadas}")
    print(f"💾 Espacio ahorrado: {ahorro_total_mb:.2f} MB")
    print("="*40 + "\n")

if __name__ == '__main__':
    # El script vive en scripts/, asi que buscamos la base un nivel arriba
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_directory = os.path.join(base_dir, 'multimedia', 'img')
    optimize_images(target_directory)
