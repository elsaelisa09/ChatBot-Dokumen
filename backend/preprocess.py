# preprocess.py
import re
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import nltk
from typing import List, Dict, Tuple
import math

nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)

def clean_text(text: str) -> str:
    """Pembersihan teks dasar"""
    print(f"\n[PREPROCESS] Memulai pembersihan teks")
    print(f"[PREPROCESS] Panjang teks asli: {len(text):,} karakter")
    
    # Lowercase
    print("[PREPROCESS] Mengubah ke huruf kecil...")
    text = text.lower()
    
    # Remove excessive whitespace dan normalize
    print("[PREPROCESS] Menormalisasi whitespace...")
    original_length = len(text)
    text = re.sub(r'\s+', ' ', text.strip())
    print(f"   - Karakter whitespace dinormalisasi: {original_length - len(text):,}")
    
    # Remove special characters tapi pertahankan struktur kalimat
    print("[PREPROCESS] Membersihkan karakter khusus...")
    original_length = len(text)
    # Pertahankan tanda baca penting untuk struktur
    text = re.sub(r'[^\w\s\.\,\!\?\;\:]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    print(f"   - Karakter khusus dihapus: {original_length - len(text):,}")
    
    print(f"[PREPROCESS] Pembersihan selesai:")
    print(f"   - Panjang teks akhir: {len(text):,} karakter")
    print(f"   - Rasio kompresi: {len(text)/original_length*100:.1f}%")
    print(f"   - Preview teks bersih (100 karakter pertama): {text[:100]}...")
    
    return text

def advanced_chunking(text: str, chunk_size: int = 500, overlap_size: int = 100, 
                     strategy: str = "overlapping") -> List[Dict]:
    """
    Advanced chunking dengan berbagai strategi
    
    Args:
        text: Teks yang akan di-chunk
        chunk_size: Ukuran chunk dalam karakter
        overlap_size: Ukuran overlap antar chunk
        strategy: Strategi chunking ('fixed', 'overlapping', 'sentence', 'adaptive')
    
    Returns:
        List of chunks dengan metadata
    """
    print(f"\n [CHUNKING] Memulai advanced chunking")
    print(f" [CHUNKING] Strategi: {strategy}")
    print(f" [CHUNKING] Ukuran chunk: {chunk_size} karakter")
    print(f" [CHUNKING] Overlap: {overlap_size} karakter")
    print(f" [CHUNKING] Panjang teks: {len(text):,} karakter")
    
    chunks = []
    
    if strategy == "fixed":
        # Fixed window chunking (seperti implementasi lama)
        for i in range(0, len(text), chunk_size):
            chunk_text = text[i:i+chunk_size]
            chunks.append({
                "text": chunk_text,
                "start_pos": i,
                "end_pos": min(i + chunk_size, len(text)),
                "strategy": "fixed",
                "word_count": len(chunk_text.split())
            })
    
    elif strategy == "overlapping":
        # Overlapping window chunking
        i = 0
        while i < len(text):
            end_pos = min(i + chunk_size, len(text))
            chunk_text = text[i:end_pos]
            
            chunks.append({
                "text": chunk_text,
                "start_pos": i,
                "end_pos": end_pos,
                "strategy": "overlapping",
                "word_count": len(chunk_text.split()),
                "overlap": overlap_size if i > 0 else 0
            })
            
            # Jika ini chunk terakhir, break
            if end_pos >= len(text):
                break
                
            # Move window dengan overlap
            i += chunk_size - overlap_size
    
    elif strategy == "sentence":
        # Sentence-based chunking dengan overlap
        sentences = sent_tokenize(text)
        current_chunk = ""
        current_start = 0
        
        for sentence in sentences:
            # Jika menambah kalimat ini tidak melebihi chunk_size
            if len(current_chunk + sentence) <= chunk_size:
                current_chunk += sentence + " "
            else:
                # Simpan chunk saat ini jika tidak kosong
                if current_chunk.strip():
                    chunks.append({
                        "text": current_chunk.strip(),
                        "start_pos": current_start,
                        "end_pos": current_start + len(current_chunk),
                        "strategy": "sentence",
                        "word_count": len(current_chunk.split()),
                        "sentence_count": len(sent_tokenize(current_chunk))
                    })
                
                # Mulai chunk baru
                current_start = current_start + len(current_chunk) - overlap_size
                current_chunk = sentence + " "
        
        # Tambahkan chunk terakhir jika ada
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "start_pos": current_start,
                "end_pos": current_start + len(current_chunk),
                "strategy": "sentence",
                "word_count": len(current_chunk.split()),
                "sentence_count": len(sent_tokenize(current_chunk))
            })
    
    elif strategy == "adaptive":
        # Adaptive chunking berdasarkan struktur teks
        # Cari paragraph breaks dan section headers
        paragraphs = text.split('\n\n')
        current_chunk = ""
        current_start = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # Jika paragraph ini fit dalam chunk size
            if len(current_chunk + para) <= chunk_size:
                current_chunk += para + "\n\n"
            else:
                # Simpan chunk saat ini jika ada
                if current_chunk.strip():
                    chunks.append({
                        "text": current_chunk.strip(),
                        "start_pos": current_start,
                        "end_pos": current_start + len(current_chunk),
                        "strategy": "adaptive",
                        "word_count": len(current_chunk.split()),
                        "paragraph_count": len([p for p in current_chunk.split('\n\n') if p.strip()])
                    })
                
                # Jika paragraph terlalu besar, bagi lagi
                if len(para) > chunk_size:
                    # Fallback ke sentence chunking untuk paragraph besar
                    sub_chunks = advanced_chunking(para, chunk_size, overlap_size, "sentence")
                    for sub_chunk in sub_chunks:
                        sub_chunk["strategy"] = "adaptive_sentence"
                        chunks.append(sub_chunk)
                    current_chunk = ""
                    current_start = current_start + len(para) + 2
                else:
                    # Mulai chunk baru dengan paragraph ini
                    current_start = current_start + len(current_chunk)
                    current_chunk = para + "\n\n"
        
        # Tambahkan chunk terakhir
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "start_pos": current_start,
                "end_pos": current_start + len(current_chunk),
                "strategy": "adaptive",
                "word_count": len(current_chunk.split()),
                "paragraph_count": len([p for p in current_chunk.split('\n\n') if p.strip()])
            })
    
    # Add chunk index dan cleanup
    for i, chunk in enumerate(chunks):
        chunk["chunk_index"] = i
        chunk["text"] = chunk["text"].strip()
    
    # Filter empty chunks
    chunks = [chunk for chunk in chunks if chunk["text"]]
    
    # Calculate statistics
    total_chars = sum(len(chunk["text"]) for chunk in chunks)
    avg_chunk_size = total_chars / len(chunks) if chunks else 0
    min_size = min(len(chunk["text"]) for chunk in chunks) if chunks else 0
    max_size = max(len(chunk["text"]) for chunk in chunks) if chunks else 0
    
    print(f" [CHUNKING] Chunking selesai:")
    print(f"   - Total chunks: {len(chunks)}")
    print(f"   - Rata-rata ukuran chunk: {avg_chunk_size:.0f} karakter")
    print(f"   - Ukuran terkecil: {min_size} karakter")
    print(f"   - Ukuran terbesar: {max_size} karakter")
    print(f"   - Total karakter: {total_chars:,}")
    
    if chunks:
        print(f" [CHUNKING] Preview chunk pertama (100 karakter): {chunks[0]['text'][:100]}...")
        if len(chunks) > 1:
            print(f" [CHUNKING] Preview chunk terakhir (100 karakter): {chunks[-1]['text'][:100]}...")
    
    return chunks

def remove_stopwords_and_tokenize(text: str) -> Tuple[str, List[str]]:
    """
    Remove stopwords dan return both cleaned text dan tokens
    Opsional untuk search optimization
    """
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words("indonesian"))
    filtered_tokens = [token for token in tokens if token.lower() not in stop_words and len(token) > 2]
    cleaned_text = " ".join(filtered_tokens)
    
    return cleaned_text, filtered_tokens
