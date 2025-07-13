import os
import fitz  # PyMuPDF

def extract_text_from_all_pdfs(folder_path):
    all_text = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"): #hanya yang berakhiran .pdf
            file_path = os.path.join(folder_path, filename)
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            all_text.append({
                "filename": filename, #nama file
                "text": text #teks mentah dari PDF
            })
    return all_text

# Contoh pemakaian langsung
if __name__ == "__main__":
    folder = "pdf"  # nama folder tempat  yang menyimpan  40 file PDF
    results = extract_text_from_all_pdfs(folder)

    print(f"Berhasil baca {len(results)} file PDF✅\n")

    # Tampilkan 500 karakter pertama dari tiap dokumen
    for doc in results:
        print(f"\n📄 {doc['filename']}")
        print(doc['text'][:200])
