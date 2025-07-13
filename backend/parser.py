# parser.py
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Users\elsae\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

def extract_text_from_pdf(file_path):
    print(f"\n[PARSER] Memulai ekstraksi teks dari PDF: {file_path}")
    
    doc = fitz.open(file_path)
    total_pages = len(doc)
    print(f"[PARSER] Dokumen memiliki {total_pages} halaman")
    
    all_text = ""
    images_processed = 0
    
    for page_num, page in enumerate(doc, 1):
        print(f"[PARSER] Mengekstrak teks dari halaman {page_num}/{total_pages}")
        page_text = page.get_text()
        all_text += page_text
        
        # Ekstrak gambar dan lakukan OCR
        images_in_page = page.get_images(full=True)
        if images_in_page:
            print(f"[PARSER] Ditemukan {len(images_in_page)} gambar di halaman {page_num}")
        
        for img_index, img in enumerate(images_in_page):
            print(f"[PARSER] Melakukan OCR pada gambar {img_index + 1}/{len(images_in_page)} di halaman {page_num}")
            base_image = doc.extract_image(img[0])
            image_bytes = base_image["image"]
            img_pil = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(img_pil)
            all_text += "\n" + text
            images_processed += 1
    
    doc.close()
    
    total_chars = len(all_text)
    print(f"[PARSER] Ekstraksi selesai:")
    print(f"   - Total halaman diproses: {total_pages}")
    print(f"   - Total gambar diproses (OCR): {images_processed}")
    print(f"   - Total karakter diekstrak: {total_chars:,}")
    print(f"   - Preview teks (100 karakter pertama): {all_text[:100]}...")
    
    return all_text
