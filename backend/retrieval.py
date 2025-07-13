# retrieval.py
import numpy as np
import faiss
from typing import List, Dict, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from collections import defaultdict
import heapq

class HybridRetriever:
    """
    Hybrid retrieval yang menggabungkan semantic search (vector) dengan keyword search (BM25/TF-IDF)
    """
    
    def __init__(self, model, chunks: List[str], metadata: List[Dict], 
                 semantic_weight: float = 0.7, keyword_weight: float = 0.3):
        self.model = model
        self.chunks = chunks
        self.metadata = metadata
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        
        # Initialize TF-IDF untuk keyword search
        print(" [RETRIEVAL] Inisialisasi TF-IDF vectorizer...")
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words=None,  # sudah handle stopwords di preprocessing
            ngram_range=(1, 2),  # Unigram dan bigram
            max_features=5000,
            lowercase=True
        )
        
        # Fit TF-IDF dengan chunks
        if chunks:
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(chunks)
            print(f" [RETRIEVAL] TF-IDF matrix dibuat: {self.tfidf_matrix.shape}")
        else:
            self.tfidf_matrix = None
        
        # FAISS index akan diset dari luar
        self.faiss_index = None
    
    def set_faiss_index(self, faiss_index):
        """Set FAISS index dari luar"""
        self.faiss_index = faiss_index
        print(f"[RETRIEVAL] FAISS index diset: {faiss_index.ntotal if faiss_index else 0} vektor")
    
    def keyword_search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Keyword-based search menggunakan TF-IDF cosine similarity
        
        Returns:
            List of (chunk_index, score) tuples
        """
        if self.tfidf_matrix is None:
            return []
        
        # Transform query dengan TF-IDF
        query_vec = self.tfidf_vectorizer.transform([query])
        
        # Hitung cosine similarity
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = [(int(idx), float(similarities[idx])) for idx in top_indices if similarities[idx] > 0]
        
        return results
    
    def semantic_search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Semantic search menggunakan FAISS vector similarity
        
        Returns:
            List of (chunk_index, similarity_distance) tuples
        """
        if self.faiss_index is None:
            return []
        
        # Embed query
        query_vec = self.model.encode([query])
        
        # Search dengan FAISS
        distances, indices = self.faiss_index.search(np.array(query_vec), top_k)
        
        # Convert distances ke similarity scores (lower distance = higher similarity)
        # Normalize distances ke range 0-1
        max_distance = np.max(distances[0]) if len(distances[0]) > 0 else 1.0
        similarities = 1.0 - (distances[0] / max_distance) if max_distance > 0 else distances[0]
        
        results = [(int(indices[0][i]), float(similarities[i])) 
                  for i in range(len(indices[0])) if indices[0][i] != -1]
        
        return results
    
    def hybrid_search(self, query: str, top_k: int = 5, 
                     rerank: bool = True) -> List[Dict]:
        """
        Hybrid search yang menggabungkan keyword dan semantic search
        
        Args:
            query: Query string
            top_k: Jumlah hasil yang diinginkan
            rerank: Whether to apply reranking
        
        Returns:
            List of result dictionaries dengan metadata
        """
        print(f"\n [HYBRID] Memulai hybrid search")
        print(f" [HYBRID] Query: {query}")
        print(f" [HYBRID] Top-K: {top_k}")
        print(f" [HYBRID] Reranking: {rerank}")
        
        # Get results dari kedua metode
        expanded_k = min(top_k * 3, 50)  # Get more candidates untuk reranking
        
        print(f" [HYBRID] TAHAP 1: Keyword search...")
        keyword_results = self.keyword_search(query, expanded_k)
        print(f" [HYBRID] Keyword results: {len(keyword_results)} chunks")
        
        print(f" [HYBRID] TAHAP 2: Semantic search...")
        semantic_results = self.semantic_search(query, expanded_k)
        print(f" [HYBRID] Semantic results: {len(semantic_results)} chunks")
        
        # Combine scores
        print(f" [HYBRID] TAHAP 3: Menggabungkan scores...")
        combined_scores = defaultdict(float)
        
        # Add keyword scores
        for chunk_idx, score in keyword_results:
            combined_scores[chunk_idx] += self.keyword_weight * score
        
        # Add semantic scores  
        for chunk_idx, score in semantic_results:
            combined_scores[chunk_idx] += self.semantic_weight * score
        
        # Sort by combined score
        sorted_results = sorted(combined_scores.items(), 
                              key=lambda x: x[1], reverse=True)[:top_k * 2]
        
        print(f" [HYBRID] Combined results: {len(sorted_results)} chunks")
        
        # Apply reranking jika diminta
        if rerank and len(sorted_results) > top_k:
            print(f" [HYBRID] TAHAP 4: Reranking...")
            sorted_results = self.rerank_results(query, sorted_results, top_k)
            print(f" [HYBRID] Reranked to: {len(sorted_results)} chunks")
        else:
            sorted_results = sorted_results[:top_k]
        
        # Build final results dengan metadata
        final_results = []
        for chunk_idx, final_score in sorted_results:
            if chunk_idx < len(self.chunks) and chunk_idx < len(self.metadata):
                result = {
                    "chunk_index": chunk_idx,
                    "text": self.chunks[chunk_idx],
                    "metadata": self.metadata[chunk_idx],
                    "combined_score": final_score,
                    "keyword_score": next((score for idx, score in keyword_results if idx == chunk_idx), 0.0),
                    "semantic_score": next((score for idx, score in semantic_results if idx == chunk_idx), 0.0)
                }
                final_results.append(result)
        
        print(f"[HYBRID] Hybrid search selesai: {len(final_results)} hasil")
        return final_results
    
    def rerank_results(self, query: str, candidates: List[Tuple[int, float]], 
                      final_k: int) -> List[Tuple[int, float]]:
        """
        Simple reranking berdasarkan exact term matches dan query coverage
        """
        query_terms = set(query.lower().split())
        reranked = []
        
        for chunk_idx, score in candidates:
            if chunk_idx < len(self.chunks):
                chunk_text = self.chunks[chunk_idx].lower()
                
                # Hitung exact matches
                exact_matches = sum(1 for term in query_terms if term in chunk_text)
                coverage = exact_matches / len(query_terms) if query_terms else 0
                
                # Boost score berdasarkan coverage
                boosted_score = score + (coverage * 0.2)  # 20% boost maksimal
                
                reranked.append((chunk_idx, boosted_score))
        
        # Sort ulang dan ambil top-k
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked[:final_k]


class QueryExpander:
    """
    Query expansion untuk meningkatkan recall
    """
    
    @staticmethod
    def expand_query(query: str) -> List[str]:
        """
        Expand query dengan variasi dan sinonim sederhana
        """
        expanded_queries = [query]  # Original query
        
        # Add variations
        query_lower = query.lower()
        
        # Add question variations
        if "apa" in query_lower:
            expanded_queries.append(query.replace("apa", "bagaimana"))
            expanded_queries.append(query.replace("apa", "sebutkan"))
        
        if "bagaimana" in query_lower:
            expanded_queries.append(query.replace("bagaimana", "apa"))
            expanded_queries.append(query.replace("bagaimana", "cara"))
        
        if "siapa" in query_lower:
            expanded_queries.append(query.replace("siapa", "nama"))
        
        # Add without question words untuk declarative search
        question_words = ["apa", "bagaimana", "siapa", "dimana", "kapan", "mengapa", "berapa"]
        words = query_lower.split()
        filtered_words = [w for w in words if w not in question_words]
        if len(filtered_words) < len(words):
            expanded_queries.append(" ".join(filtered_words))
        
        return list(set(expanded_queries))  # Remove duplicates


class DocumentLevelRetriever:
    """
    Document-level retrieval untuk ringkasan dan analisis dokumen spesifik
    """
    
    def __init__(self, chunks: List[str], metadata: List[Dict]):
        self.chunks = chunks
        self.metadata = metadata
        
        # Index chunks by filename
        self.file_to_chunks = defaultdict(list)
        for i, meta in enumerate(metadata):
            if i < len(chunks):
                self.file_to_chunks[meta["filename"]].append({
                    "index": i,
                    "text": chunks[i],
                    "metadata": meta
                })
    
    def get_chunks_by_file(self, filename: str) -> List[Dict]:
        """Get all chunks untuk file tertentu"""
        return self.file_to_chunks.get(filename, [])
    
    def get_all_files(self) -> List[str]:
        """Get list semua filename yang tersedia"""
        return list(self.file_to_chunks.keys())
    
    def summarize_document(self, filename: str, max_chunks: int = 10) -> List[Dict]:
        """
        Get chunks untuk document summarization
        Prioritaskan chunk awal dan akhir dokumen
        """
        file_chunks = self.get_chunks_by_file(filename)
        
        if len(file_chunks) <= max_chunks:
            return file_chunks
        
        # Ambil chunk awal, tengah, dan akhir
        start_chunks = file_chunks[:max_chunks//3]
        end_chunks = file_chunks[-(max_chunks//3):]
        middle_start = len(file_chunks) // 2 - (max_chunks//6)
        middle_end = len(file_chunks) // 2 + (max_chunks//6)
        middle_chunks = file_chunks[middle_start:middle_end]
        
        selected_chunks = start_chunks + middle_chunks + end_chunks
        
        # Remove duplicates sambil preserve order
        seen = set()
        result = []
        for chunk in selected_chunks:
            if chunk["index"] not in seen:
                result.append(chunk)
                seen.add(chunk["index"])
        
        return result[:max_chunks]


def create_enhanced_retrieval_system(model, chunks: List[str], metadata: List[Dict], 
                                   faiss_index=None) -> Dict:
    """
    Factory function untuk membuat enhanced retrieval system
    """
    print(f"\n [RETRIEVAL] Membuat enhanced retrieval system")
    
    # Create hybrid retriever
    hybrid_retriever = HybridRetriever(model, chunks, metadata)
    if faiss_index:
        hybrid_retriever.set_faiss_index(faiss_index)
    
    # Create document-level retriever
    doc_retriever = DocumentLevelRetriever(chunks, metadata)
    
    # Create query expander
    query_expander = QueryExpander()
    
    print(f" [RETRIEVAL] Enhanced retrieval system siap:")
    print(f"   - Hybrid search:  (semantic + keyword)")
    print(f"   - Document-level retrieval: ")
    print(f"   - Query expansion: ")
    print(f"   - Files available: {len(doc_retriever.get_all_files())}")
    
    return {
        "hybrid": hybrid_retriever,
        "document": doc_retriever,
        "expander": query_expander
    }
