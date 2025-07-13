import os
import re
import fitz  # PyMuPDF
import nltk
from nltk.tokenize import sent_tokenize
import pickle

nltk.download("punkt")

MAX_TOKENS = 500

def count_tokens(text):
    return len(text.split())

def load_pdf_text(file_path):
    print(f"DEBUG: Sedang memuat teks dari '{os.path.basename(file_path)}'...")
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        print(f"DEBUG: Selesai memuat teks. Total karakter: {len(text)}")
        return text
    except Exception as e:
        print(f"ERROR: Gagal memuat teks dari '{file_path}': {e}")
        return ""
#Untuk mengekstrak tanggal dari teks,  menggunakan regex untuk menemukan pola tanggal yang umum
# dan kemudian mengembalikan kalimat-kalimat yang mengandung tanggal tersebut sebagai chunk
def extract_date_chunks(text):
    date_pattern = r"\b\d{1,2}[-/\s]\d{1,2}[-/\s]\d{2,4}\b"
    matches = list(re.finditer(date_pattern, text))
    sentences = sent_tokenize(text)
    chunks = []
    for match in matches:
        for i, sentence in enumerate(sentences):
            if match.group() in sentence:
                context = sentences[max(0, i-1):i+2]  # 1 kalimat sebelum dan sesudah
                chunks.append(" ".join(context))
                break
    return chunks

def split_by_pasal(text):
    # Perbaikan: hanya deteksi PASAL yang benar-benar judul pasal, bukan referensi
    # Pattern yang lebih spesifik untuk judul pasal dokumen
    pasal_chunks = re.split(r"(?=^PASAL\s+[1-9]\d*\s*$)", text, flags=re.IGNORECASE | re.MULTILINE)
    result = []
    for chunk in pasal_chunks:
        chunk = chunk.strip()
        if chunk:
            # Extract pasal number from chunk content, hanya untuk judul pasal yang valid
            pasal_match = re.search(r"^PASAL\s+([1-9]\d*)", chunk, flags=re.IGNORECASE | re.MULTILINE)
            pasal_number = int(pasal_match.group(1)) if pasal_match else None
            result.append((chunk, pasal_number))
    return result

def split_into_chunks(text, source_name):
    if not text:
        print(f"DEBUG: Teks kosong dari '{source_name}', tidak ada chunk yang dibuat.")
        return [], []

    chunks = []
    metadatas = []
    owner = os.path.splitext(source_name)[0].strip()  # Tambah .strip() untuk menghilangkan trailing spaces

    # --- Tambah: Chunk tanggal penting ---
    date_chunks = extract_date_chunks(text)
    for chunk in date_chunks:
        chunks.append(chunk)
        metadatas.append({"owner": owner, "type": "tanggal"})

    # --- Tambah: Chunk PASAL ---
    pasal_sections = split_by_pasal(text)
    for chunk, pasal_number in pasal_sections:
        chunks.append(chunk)
        if pasal_number:
            metadatas.append({"owner": owner, "type": "pasal", "pasal": f"PASAL {pasal_number}"})
        else:
            metadatas.append({"owner": owner, "type": "umum"})  # fallback untuk chunk tanpa pasal

    # --- Tambah: Chunk umum ---
    all_sentences = sent_tokenize(text)
    i = 0
    while i < len(all_sentences):
        current_chunk = []
        token_count = 0
        while i < len(all_sentences) and token_count + count_tokens(all_sentences[i]) <= MAX_TOKENS:
            current_chunk.append(all_sentences[i])
            token_count += count_tokens(all_sentences[i])
            i += 1
        chunk_text = " ".join(current_chunk).strip()
        if chunk_text:
            chunks.append(chunk_text)
            metadatas.append({"owner": owner, "type": "umum"})

    print(f"DEBUG: Selesai chunking '{source_name}'. Total chunks: {len(chunks)}")
    return chunks, metadatas

def chunk_all_pdfs(pdf_folder):
    all_chunks = []
    all_metadatas = []

    if not os.path.isdir(pdf_folder):
        print(f"ERROR: Folder '{pdf_folder}' tidak ditemukan.")
        return [], []

    print(f"\n\U0001F4C2 Memulai proses chunking untuk semua PDF di folder: '{pdf_folder}'")
    for filename in os.listdir(pdf_folder):
        if filename.endswith(".pdf"):
            path = os.path.join(pdf_folder, filename)
            print(f"\n\U0001F4C4 Memproses file: {filename}")
            text = load_pdf_text(path)
            if text:
                chunks, metadatas = split_into_chunks(text, filename)
                all_chunks.extend(chunks)
                all_metadatas.extend(metadatas)
            else:
                print(f"SKIP: File '{filename}' tidak diproses karena gagal membaca teks.")

    return all_chunks, all_metadatas

if __name__ == "__main__":
    pdf_directory = "pdf"
    all_chunks, all_metadatas = chunk_all_pdfs(pdf_directory)

    print(f"\n Selesai memproses semua PDF")
    print(f"\U0001F4DA Total chunk: {len(all_chunks)} dari {len(set(meta['owner'] for meta in all_metadatas))} file\n")

    if all_chunks:
        print("--- Contoh 5 chunk pertama ---")
        for i, chunk in enumerate(all_chunks[:5]):
            meta = all_metadatas[i]
            print(f"\n\U0001F4CC Chunk {i+1} dari '{meta['owner']}', Type: {meta['type']}\n{chunk[:300]}...\n")

    with open("doc_chunks.pkl", "wb") as f:
        pickle.dump({"chunks": all_chunks, "metadatas": all_metadatas}, f)

    print("\n\U0001F4BE File 'doc_chunks.pkl' berhasil disimpan!")
