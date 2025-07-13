import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

# === Load model embedding ===
print("Memuat model embedding...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# === Load chunks dan metadata dari file pickle ===
print("Membaca data dari 'doc_chunks.pkl'...")
with open("doc_chunks.pkl", "rb") as f:
    data = pickle.load(f)
    chunks = data["chunks"]
    metadatas = data["metadatas"]

if not chunks:
    print("Tidak ada chunk ditemukan di file❌ ")
    exit()

print(f"Total chunk yang ditemukan: {len(chunks)}")
print(f"Contoh owner pertama: {metadatas[0].get('owner', 'N/A')}")

# === Buat embedding untuk setiap chunk ===
print("Membuat embedding untuk setiap chunk...")
embeddings = model.encode(chunks, show_progress_bar=True)
embeddings = np.array(embeddings).astype("float32")

# === Buat FAISS index ===
print("Loading index FAISS...")
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

# === Simpan FAISS index dan metadata ===
faiss.write_index(index, "doc_index.faiss")
with open("doc_chunks.pkl", "wb") as f:
    pickle.dump({
        "chunks": chunks,
        "metadatas": metadatas
    }, f)

print("Index dan metadata berhasil disimpan!")
print("File: doc_index.faiss + doc_chunks.pkl")

# === Verifikasi index ===
index = faiss.read_index("doc_index.faiss")
print(f"🔍 Total vektor di index: {index.ntotal}")
print(f"🔍 Dimensi vektor: {index.d}")
