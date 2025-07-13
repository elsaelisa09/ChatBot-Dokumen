import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from difflib import get_close_matches
import spacy
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from rank_bm25 import BM25Okapi
import string
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# === Load FAISS index dan metadata ===
print("Memuat index dan metadata...")
index = faiss.read_index("doc_index.faiss")
with open("doc_chunks.pkl", "rb") as f:
    data = pickle.load(f)

chunks = data["chunks"]
metadatas = data["metadatas"]

# === Load embedding model ===
model = SentenceTransformer("all-MiniLM-L6-v2")

# === Setup OpenAI Client untuk DeepSeek Chat V3 ===
client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.getenv("OPENAI_API_KEY", "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"),
    timeout=30.0  # Tambah timeout
)

# === Test Koneksi API ===
def test_api_connection():
    """Test koneksi ke DeepSeek Chat V3 API"""
    try:
        print("🔍 Testing koneksi ke DeepSeek Chat V3...")
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://aiPintar.local",
                "X-Title": "AI Pintar Document QA System",
            },
            model=os.getenv("MODEL_NAME", "deepseek/deepseek-chat-v3-0324:free"),
            messages=[
                {"role": "user", "content": "Hello, please respond with 'API connection successful'"}
            ],
            max_tokens=50
        )
        print("Koneksi API berhasil!")
        return True
    except Exception as e:
        print(f"Test koneksi gagal: {e}")
        print("Silakan cek:")
        print("   1. Koneksi internet")
        print("   2. Firewall settings")
        print("   3. VPN jika diperlukan")
        return False

# === Load spaCy NER ===
print("Memuat model NER spaCy...")
nlp = spacy.load("en_core_web_sm")

# === Ambil daftar owner unik ===
all_owners = list(set(meta["owner"] for meta in metadatas if isinstance(meta, dict) and "owner" in meta))

# === Preprocessing Functions ===
def preprocess_text(text):
    """
    Preprocessing text: lowercase, tokenisasi, hapus stopwords dan punctuation
    """
    if not text:
        return []
    
    try:
        # Download nltk data jika belum ada
        try:
            stopwords.words('indonesian')
        except LookupError:
            nltk.download('stopwords', quiet=True)
            nltk.download('punkt', quiet=True)
    except:
        pass
    
    # Lowercase
    text = text.lower()
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove punctuation and stopwords
    try:
        stop_words = set(stopwords.words('english')) | set(stopwords.words('indonesian'))
    except:
        stop_words = set(stopwords.words('english'))
    
    tokens = [token for token in tokens if token not in string.punctuation and token not in stop_words and len(token) > 2]
    
    return tokens

def preprocess_query(query):
    """
    Preprocessing untuk query: lowercase, tokenisasi
    """
    return preprocess_text(query)

def preprocess_chunks_for_bm25(chunks):
    """
    Preprocessing semua chunks untuk BM25
    """
    return [preprocess_text(chunk) for chunk in chunks]

def hybrid_retrieval(query, owner_chunks, top_k=5):
    """
    Hybrid retrieval menggunakan BM25 + FAISS untuk pertanyaan bebas
    """
    try:
        # Preprocessing query
        processed_query = preprocess_text(query)
        
        # Preprocessing semua chunk untuk BM25
        processed_chunks = []
        chunk_texts = []
        for chunk in owner_chunks:
            processed_chunk = preprocess_text(chunk['text'])
            processed_chunks.append(processed_chunk)
            chunk_texts.append(chunk['text'])
        
        if not processed_chunks:
            return []
        
        # Inisialisasi BM25
        bm25 = BM25Okapi(processed_chunks)
        
        # Hitung skor BM25
        bm25_scores = bm25.get_scores(processed_query)
        
        # Hitung FAISS similarity
        query_embedding = model.encode([query])
        
        faiss_scores = []
        for chunk_text in chunk_texts:
            chunk_embedding = model.encode([chunk_text])
            # Cosine similarity
            similarity = np.dot(query_embedding[0], chunk_embedding[0]) / (
                np.linalg.norm(query_embedding[0]) * np.linalg.norm(chunk_embedding[0])
            )
            faiss_scores.append(similarity)
        
        faiss_scores = np.array(faiss_scores)
        
        # Normalisasi skor (0-1)
        if len(bm25_scores) > 1 and np.max(bm25_scores) > np.min(bm25_scores):
            bm25_scores_norm = (bm25_scores - np.min(bm25_scores)) / (np.max(bm25_scores) - np.min(bm25_scores))
        else:
            bm25_scores_norm = np.ones_like(bm25_scores)
            
        if len(faiss_scores) > 1 and np.max(faiss_scores) > np.min(faiss_scores):
            faiss_scores_norm = (faiss_scores - np.min(faiss_scores)) / (np.max(faiss_scores) - np.min(faiss_scores))
        else:
            faiss_scores_norm = np.ones_like(faiss_scores)
        
        # Gabungkan skor (weighted average: 40% BM25 + 60% FAISS)
        combined_scores = 0.4 * bm25_scores_norm + 0.6 * faiss_scores_norm
        
        # Ambil top_k chunks dengan skor tertinggi
        top_indices = np.argsort(combined_scores)[::-1][:top_k]
        
        # Return chunks dengan skor
        result_chunks = []
        for idx in top_indices:
            chunk_data = owner_chunks[idx].copy()
            chunk_data['bm25_score'] = float(bm25_scores[idx])
            chunk_data['faiss_score'] = float(faiss_scores[idx])
            chunk_data['combined_score'] = float(combined_scores[idx])
            result_chunks.append(chunk_data)
        
        print(f"🔍 Hybrid retrieval: {len(result_chunks)} chunks retrieved")
        for i, chunk in enumerate(result_chunks):
            print(f"  Chunk {i+1}: BM25={chunk['bm25_score']:.3f}, FAISS={chunk['faiss_score']:.3f}, Combined={chunk['combined_score']:.3f}")
        
        return result_chunks
        
    except Exception as e:
        print(f"❌ Error dalam hybrid retrieval: {e}")
        # Fallback: ambil 5 chunk pertama
        return owner_chunks[:top_k]

# === Deteksi nama owner dari pertanyaan ===
def detect_owner_from_question(question):
    # Preprocessing: hapus kata-kata yang tidak relevan untuk deteksi nama
    excluded_words = ['rangkum', 'pasal', 'dari', 'tentang', 'summary', 'rangkuman']
    
    doc = nlp(question)
    person_names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    
    # Filter person_names yang valid (tidak mengandung kata-kata excluded)
    valid_names = []
    for name in person_names:
        if not any(word in name.lower() for word in excluded_words):
            valid_names.append(name)
    
    # Coba match dengan nama yang valid
    for name in valid_names:
        match = get_close_matches(name, all_owners, n=1, cutoff=0.6)
        if match:
            print(f"Matched '{name}' → '{match[0]}'")
            return match[0]
    
    # Fallback: cari fuzzy match langsung dari seluruh pertanyaan
    for owner in all_owners:
        if owner.lower() in question.lower():
            print(f"Direct match found: '{owner}'")
            return owner
    
    # Last resort: fuzzy matching dengan pertanyaan
    match = get_close_matches(question, all_owners, n=1, cutoff=0.4)
    if match:
        print(f"Fuzzy match: '{match[0]}'")
        return match[0]
    
    return None

# === Klasifikasi jenis pertanyaan ===
def detect_question_type(question):
    q = question.lower()
    if any(k in q for k in ["rangkum", "rangkuman", "ringkasan", "summary", "kesimpulan", "intisari", "rangkuman dokumen"]):
        return "define_rangkuman"
    if any(k in q for k in ["tanggal penting", "tanggal", "kapan", "ditandatangani"]):
        return "define_tanggal"
    if any(k in q for k in ["luas lahan", "luas properti", "dimana lokasi", "lokasi properti", "berapa luas"]) and "rambah" not in q:
        return "define_luas_lokasi"
    if any(k in q for k in ["area rambah", "lahan rambah", "lokasi rambah", "luas rambah"]):
        return "define_luas_area_rambah"
    if re.search(r'pasal\s+\d+', q):
        return "define_pasal"
    return "free"

# === Ambil nomor pasal dari pertanyaan (jika ada) ===
def extract_pasal_index(question):
    match = re.search(r'pasal\s+(\d+)', question.lower())
    if match:
        return int(match.group(1))
    return None

# === Proses pertanyaan ===
def ask_question(question, top_k=5):
    print(f"❓ Pertanyaan: {question}")

    owner = detect_owner_from_question(question)
    if not owner:
        return "Tidak bisa mendeteksi nama pemilik dari pertanyaan. Harap sebutkan nama lengkapnya."
    print(f"Deteksi owner: {owner}")

    qtype = detect_question_type(question)
    print(f"Jenis pertanyaan: {qtype}")

    # Filter semua chunk milik owner
    filtered = [(i, chunk, meta) for i, (chunk, meta) in enumerate(zip(chunks, metadatas))
                if meta.get("owner", "").lower() == owner.lower()]
    if not filtered:
        return f" Tidak ditemukan dokumen milik '{owner}'."

    selected_contexts = []

    if qtype == "define_rangkuman":
        selected_contexts = [chunk for _, chunk, _ in filtered]

    elif qtype == "define_tanggal":
        # Untuk pertanyaan tanggal, ambil HANYA chunk pertama dari dokumen (informasi tanggal ada di chunk pertama)
        sorted_filtered = sorted(filtered, key=lambda x: x[0])  # Sort by original index
        if sorted_filtered:
            selected_contexts = [sorted_filtered[0][1]]  # Ambil hanya chunk pertama
            print(f"Mengambil chunk pertama dokumen untuk mencari tanggal pembuatan perjanjian")

    elif qtype == "define_luas_lokasi":
        # Untuk pertanyaan luas dan lokasi, ambil chunk ke-2 dari dokumen (informasi ada di chunk ke-2)
        sorted_filtered = sorted(filtered, key=lambda x: x[0])  # Sort by original index
        if len(sorted_filtered) >= 2:
            selected_contexts = [sorted_filtered[1][1]]  # Ambil chunk ke-2 (index 1)
            print(f"Mengambil chunk ke-2 dokumen untuk mencari luas dan lokasi properti")
        elif sorted_filtered:
            selected_contexts = [sorted_filtered[0][1]]  # Fallback ke chunk pertama jika hanya ada 1 chunk
            print(f"Fallback: Mengambil chunk pertama (hanya ada 1 chunk tersedia)")

    elif qtype == "define_luas_area_rambah":
        # Untuk pertanyaan area rambah, ambil chunk ke-2 dari dokumen (strategi sama dengan luas lokasi)
        sorted_filtered = sorted(filtered, key=lambda x: x[0])  # Sort by original index
        if len(sorted_filtered) >= 2:
            selected_contexts = [sorted_filtered[1][1]]  # Ambil chunk ke-2 (index 1)
            print(f"Mengambil chunk ke-2 dokumen untuk mencari luas dan lokasi area rambah")
        elif sorted_filtered:
            selected_contexts = [sorted_filtered[0][1]]  # Fallback ke chunk pertama jika hanya ada 1 chunk
            print(f" Fallback: Mengambil chunk pertama (hanya ada 1 chunk tersedia)")

    elif qtype == "define_pasal":
        target_index = extract_pasal_index(question)
        if target_index is not None:
            target_pasal = f"PASAL {target_index}"
            selected_contexts = [chunk for _, chunk, meta in filtered
                                 if meta.get("pasal") == target_pasal]
            print(f" Mengambil chunk dengan pasal == '{target_pasal}'")

    else:
        # Free question → hybrid retrieval (BM25 + FAISS)
        print("Melakukan hybrid retrieval (BM25 + FAISS)...")
        
        # Siapkan owner chunks dalam format yang diperlukan untuk hybrid retrieval
        owner_chunks = []
        for i, chunk, meta in filtered:
            owner_chunks.append({
                'text': chunk,
                'index': i,
                'metadata': meta
            })
        
        if owner_chunks:
            # Gunakan hybrid retrieval
            result_chunks = hybrid_retrieval(question, owner_chunks, top_k=top_k)
            selected_contexts = [chunk_data['text'] for chunk_data in result_chunks]
        else:
            selected_contexts = []

    if not selected_contexts:
        return f" Tidak ditemukan informasi yang cocok di dokumen milik '{owner}'."

    context = "\n---\n".join(selected_contexts)

    # Adaptive system prompt based on question type
    if qtype == "define_rangkuman":
        system_prompt = (
            "Berikan rangkuman komprehensif dari dokumen ini. Jangan memberikan informasi tambahan di luar dokumen. "
            "Buatlah rangkuman dalam 5 poin penjelasan singkat yang merangkum keseluruhan isi dokumen. "
            "Setiap poin harus mencakup aspek penting dari dokumen seperti pihak-pihak yang terlibat, "
            "ruang lingkup pekerjaan, jangka waktu, dan ketentuan-ketentuan utama."
        )
    elif qtype == "define_tanggal": #untuk tanggal p,pembuatan erjanjian
        system_prompt = (
            "Berdasarkan dokumen, temukan kapan perjanjian dibuat. "
            "Cari kalimat yang dimulai dengan 'Pada hari ini' dan ekstrak informasi tanggal. "
            "Jawab dengan format: 'Dokumen perjanjian ini dibuat pada [hari], tanggal [tanggal] bulan [bulan] tahun [tahun].' "
            "Contoh: 'Dokumen perjanjian ini dibuat pada Jumat, tanggal 8 bulan Agustus tahun 2024.'"
        )
    elif qtype == "define_luas_lokasi":
        system_prompt = (
        "Berdasarkan dokumen, temukan informasi tentang luas lahan dan lokasi properti UTAMA yang menjadi objek perjanjian. "
        "JANGAN ambil alamat personal pemilik. Fokus hanya pada properti UTAMA (yang disebut pertama atau sebagai objek dalam surat perjanjian). "
        "ABAIAKAN informasi lain seperti lahan/penggarapan/perambahan tambahan, meskipun memiliki ukuran dan lokasi. "
        "Cari informasi: "
        "1. Luas lahan properti utama (biasanya dalam satuan m²) "
        "2. Lokasi properti utama (biasanya berupa nama jalan, gang, persil, atau area tertentu) "
        "Tandai sebagai 'Properti' atau 'Objek Perjanjian', bukan 'Area Dirambah' atau sejenisnya. "
        "Jawab dengan format persis: 'Luas lahan properti: [luas] m². Lokasi properti: [lokasi properti saja].'"
        )
    elif qtype == "define_luas_area_rambah":
        system_prompt = (
            "Berdasarkan dokumen, temukan informasi tentang luas dan lokasi area rambah. "
            "JANGAN ambil informasi properti utama atau alamat personal pemilik. Cari informasi tentang: "
            "1. Luas area rambah yang biasanya dinyatakan dalam m2 "
            "2. Lokasi area rambah (biasanya berbeda dari properti utama) "
            "Fokus khusus pada area yang dirambah, bukan properti utama. "
            "Jawab dengan format: 'Luas area rambah: [luas] m2. Lokasi area rambah: [lokasi area rambah].'"
        )
    elif qtype == "define_pasal":
        system_prompt = (
            "Kamu adalah asisten AI cerdas. Jawablah pertanyaan tentang pasal dengan ringkasan yang jelas dan terstruktur. "
            "Jika tidak ditemukan jawabannya, balas: 'Informasi tidak ditemukan dalam dokumen.'"
        )
    else:
        system_prompt = (
            "Kamu adalah asisten AI cerdas. Jawablah pertanyaan hanya berdasarkan dokumen di bawah. "
            "Jika tidak ditemukan jawabannya, balas: 'Informasi tidak ditemukan dalam dokumen.'"
        )

    print(" Mengirim ke model DeepSeek Chat V3...")
    try:
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://aiPintar.local",
                "X-Title": "AI Pintar Document QA System",
            },
            model=os.getenv("MODEL_NAME", "deepseek/deepseek-chat-v3-0324:free"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Dokumen:\n{context}\n\nPertanyaan:\n{question}"}
            ],
            timeout=30.0  # Tambah timeout
        )
        return response.choices[0].message.content
    
    except Exception as e:
        print(f" Error saat menghubungi DeepSeek Chat V3: {e}")
        print("🔧Kemungkinan penyebab:")
        print("   1. Masalah koneksi internet")
        print("   2. API key tidak valid")
        print("   3. Firewall blocking request")
        print("   4. Service OpenRouter sedang down")
        return f"Gagal mendapatkan respons dari AI: {str(e)}"

# === CLI Loop ===
if __name__ == "__main__":
    print(" Sistem QnA Dokumen Berbasis DeepSeek Chat V3 + Define-aware Retrieval Siap Digunakan.")
    
    # Test koneksi API terlebih dahulu
    if not test_api_connection():
        print("\n Tidak dapat melanjutkan tanpa koneksi API yang valid.")
        print(" Alternatif: Gunakan kembali Ollama lokal jika tersedia.")
        exit(1)
    
    while True:
        q = input("\n❓ Masukkan pertanyaan (atau ketik 'exit'): ")
        if q.lower() == "exit":
            break
        jawab = ask_question(q)
        print(f"\n Jawaban:\n{jawab}")
