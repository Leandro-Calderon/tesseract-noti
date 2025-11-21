#!/usr/bin/env python3
"""
OCR optimizado para documentos legales (notas y resoluciones)
- Rápido en equipos de bajos recursos
- Optimizado para texto con tipografía estándar
"""

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path
import sys
import time
import re


def preprocess_image(img: Image.Image) -> Image.Image:
    """
    Preprocesar imagen para mejor OCR
    Optimizado para documentos escaneados
    """
    # Convertir a escala de grises
    img = img.convert('L')
    
    # Aumentar contraste (mejora texto débil)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    
    # Aumentar nitidez
    img = img.filter(ImageFilter.SHARPEN)
    
    # Binarización (blanco/negro puro) - opcional
    # threshold = 128
    # img = img.point(lambda p: 255 if p > threshold else 0)
    
    return img


def clean_text(text: str) -> str:
    """
    Limpiar texto extraído
    - Eliminar espacios extras
    - Normalizar saltos de línea
    """
    # Eliminar múltiples espacios
    text = re.sub(r' +', ' ', text)
    
    # Eliminar múltiples saltos de línea (dejar máximo 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Eliminar espacios al inicio/fin de cada línea
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    return text.strip()


def ocr_documento_legal(
    image_path: str,
    preprocess: bool = True,
    save_preprocessed: bool = False
) -> str:
    """
    Extraer texto de documento legal
    
    Args:
        image_path: Ruta a la imagen
        preprocess: Aplicar preprocesamiento (mejora calidad)
        save_preprocessed: Guardar imagen preprocesada
    
    Returns:
        Texto extraído
    """
    print(f"📄 Procesando documento legal: {Path(image_path).name}")
    
    start = time.time()
    
    # Cargar imagen
    img = Image.open(image_path)
    img_size = img.size
    file_size = Path(image_path).stat().st_size / 1024  # KB
    
    print(f"📐 Tamaño: {img_size[0]}x{img_size[1]} px ({file_size:.1f} KB)")
    
    # Preprocesar si está habilitado
    if preprocess:
        print("⚙️  Preprocesando imagen...")
        img_processed = preprocess_image(img)
        
        if save_preprocessed:
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            preprocessed_path = output_dir / f"{Path(image_path).stem}_preprocessed.png"
            img_processed.save(preprocessed_path)
            print(f"💾 Imagen preprocesada guardada: {preprocessed_path}")
    else:
        img_processed = img
    
    # Configuración de Tesseract para documentos
    custom_config = r'--oem 3 --psm 6'
    # --oem 3: LSTM + Legacy engine (más preciso)
    # --psm 6: Assume a single uniform block of text (documentos)
    # Otras opciones de psm:
    #   --psm 1: Automatic page segmentation with OSD
    #   --psm 3: Fully automatic page segmentation (default)
    #   --psm 4: Assume a single column of text
    
    # Extraer texto
    print("⏳ Extrayendo texto (español + inglés)...")
    text = pytesseract.image_to_string(
        img_processed,
        lang='spa+eng',
        config=custom_config
    )
    
    # Limpiar texto
    text = clean_text(text)
    
    elapsed = time.time() - start
    
    # Estadísticas
    lines = len([l for l in text.split('\n') if l.strip()])
    words = len(text.split())
    chars = len(text)
    
    print(f"\n{'='*60}")
    print(f"✅ Completado en {elapsed:.2f} segundos")
    print(f"{'='*60}")
    print(f"📊 Estadísticas:")
    print(f"   - Líneas: {lines}")
    print(f"   - Palabras: {words}")
    print(f"   - Caracteres: {chars}")
    print(f"{'='*60}\n")
    
    return text


def save_results(text: str, image_path: str, include_metadata: bool = True):
    """Guardar resultados en múltiples formatos"""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    base_name = Path(image_path).stem
    
    # Texto plano
    txt_file = output_dir / f"{base_name}.txt"
    txt_file.write_text(text, encoding='utf-8')
    print(f"💾 Guardado: {txt_file}")
    
    # Markdown (opcional, con metadatos)
    if include_metadata:
        md_file = output_dir / f"{base_name}.md"
        md_content = f"""# Documento: {base_name}

**Fuente:** `{Path(image_path).name}`  
**Fecha de procesamiento:** {time.strftime('%Y-%m-%d %H:%M:%S')}

---

{text}
"""
        md_file.write_text(md_content, encoding='utf-8')
        print(f"💾 Guardado: {md_file}")


def process_batch(input_dir: str = "input", preprocess: bool = True):
    """Procesar todos los documentos de una carpeta"""
    input_path = Path(input_dir)
    
    # Buscar imágenes
    extensions = ['*.png', '*.jpg', '*.jpeg', '*.tiff', '*.bmp']
    images = []
    for ext in extensions:
        images.extend(input_path.glob(ext))
    
    if not images:
        print(f"❌ No se encontraron imágenes en {input_dir}/")
        return
    
    print(f"📁 Encontrados {len(images)} documentos")
    print(f"{'='*60}\n")
    
    total_start = time.time()
    
    for i, img_path in enumerate(images, 1):
        print(f"[{i}/{len(images)}] {img_path.name}")
        print("-" * 60)
        
        try:
            text = ocr_documento_legal(str(img_path), preprocess=preprocess)
            save_results(text, str(img_path))
            print()
        except Exception as e:
            print(f"❌ Error: {e}\n")
            continue
    
    total_elapsed = time.time() - total_start
    avg_time = total_elapsed / len(images)
    
    print(f"\n{'='*60}")
    print(f"✨ Proceso completado!")
    print(f"⏱️  Tiempo total: {total_elapsed:.2f} segundos")
    print(f"⏱️  Promedio por documento: {avg_time:.2f} segundos")
    print(f"{'='*60}")


def main():
    if len(sys.argv) < 2:
        print("""
Uso: python ocr_legal.py <imagen|directorio> [opciones]

Ejemplos:
  python ocr_legal.py input/nota.png              # Procesar una imagen
  python ocr_legal.py input/                      # Procesar todas las imágenes
  python ocr_legal.py input/nota.png --no-prep    # Sin preprocesamiento
  python ocr_legal.py input/ --save-prep          # Guardar imágenes preprocesadas

Opciones:
  --no-prep       Desactivar preprocesamiento de imagen
  --save-prep     Guardar imágenes preprocesadas
        """)
        sys.exit(1)
    
    path = sys.argv[1]
    preprocess = '--no-prep' not in sys.argv
    save_preprocessed = '--save-prep' in sys.argv
    
    # Verificar si es directorio o archivo
    path_obj = Path(path)
    
    if not path_obj.exists():
        print(f"❌ No existe: {path}")
        sys.exit(1)
    
    if path_obj.is_dir():
        # Procesar batch
        process_batch(str(path_obj), preprocess=preprocess)
    else:
        # Procesar archivo individual
        text = ocr_documento_legal(
            path,
            preprocess=preprocess,
            save_preprocessed=save_preprocessed
        )
        print(text)
        print()
        save_results(text, path)


if __name__ == "__main__":
    main()

