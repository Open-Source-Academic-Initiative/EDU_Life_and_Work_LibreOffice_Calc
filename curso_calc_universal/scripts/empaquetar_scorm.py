import os
import zipfile

def create_scorm_zip():
    # El script vive en scripts/, asi que la raiz es un nivel arriba
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_filename = os.path.join(base_dir, 'Curso_Calc_LaUniversal_SCORM.zip')
    
    print(f"\nIniciando empaquetado SCORM en: {output_filename}\n")
    
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
            
    print("\n✅ EMPAQUETADO EXITOSO. Sube el archivo .zip a tu Moodle.\n")

if __name__ == "__main__":
    create_scorm_zip()
