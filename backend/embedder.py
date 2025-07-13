# embedder.py
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_chunks(chunks):
    print(f"[EMBEDDER] Jumlah chunks untuk di-embed: {len(chunks)}")
    
    embeddings = model.encode(chunks)
    
    print(f"[EMBEDDER] Embedding selesai:")
    print(f"   - Dimensi embedding: {embeddings.shape}")
    print(f"   - Ukuran setiap embedding: {embeddings.shape[1]} dimensi")
    
    print("[EMBEDDER] Membuat FAISS index...")
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    
    print(f"[EMBEDDER] FAISS index berhasil dibuat dengan {index.ntotal} vektor")
    
    return index, embeddings
