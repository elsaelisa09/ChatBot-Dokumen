# delete_manager.py - Dedicated DELETE Operations Manager

import os
import json
import pickle
import faiss
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeleteManager:
    """Manages file deletion operations for DocNLP RAG System"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.upload_dir = os.path.join(base_dir, "storage", "uploads")
        self.index_dir = os.path.join(base_dir, "storage", "index")
        
        # File paths
        self.faiss_index_path = os.path.join(self.index_dir, "faiss_index.bin")
        self.metadata_path = os.path.join(self.index_dir, "metadata.json")
        self.files_info_path = os.path.join(self.index_dir, "files_info.json")
        self.chunks_path = os.path.join(self.index_dir, "chunks.pkl")
    
    def load_system_data(self) -> tuple:
        """Load current system data"""
        try:
            # Load FAISS index
            index = None
            if os.path.exists(self.faiss_index_path):
                index = faiss.read_index(self.faiss_index_path)
            
            # Load chunks
            chunks = []
            if os.path.exists(self.chunks_path):
                with open(self.chunks_path, 'rb') as f:
                    chunks = pickle.load(f)
            
            # Load metadata
            metadata = []
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            # Load files info
            files_info = {}
            if os.path.exists(self.files_info_path):
                with open(self.files_info_path, 'r', encoding='utf-8') as f:
                    files_info = json.load(f)
            
            return index, chunks, metadata, files_info
            
        except Exception as e:
            logger.error(f"Error loading system data: {e}")
            return None, [], [], {}
    
    def save_system_data(self, index, chunks: List, metadata: List, files_info: Dict) -> bool:
        """Save updated system data"""
        try:
            # Save FAISS index
            if index is not None:
                faiss.write_index(index, self.faiss_index_path)
            elif os.path.exists(self.faiss_index_path):
                os.remove(self.faiss_index_path)
            
            # Save chunks
            with open(self.chunks_path, 'wb') as f:
                pickle.dump(chunks, f)
            
            # Save metadata
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Save files info
            with open(self.files_info_path, 'w', encoding='utf-8') as f:
                json.dump(files_info, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving system data: {e}")
            return False
    
    def rebuild_index(self, chunks: List, model) -> Optional[Any]:
        """Rebuild FAISS index from chunks"""
        if not chunks:
            return None
        
        try:
            logger.info(f"Rebuilding FAISS index for {len(chunks)} chunks...")
            embeddings = model.encode(chunks)
            
            new_index = faiss.IndexFlatL2(embeddings.shape[1])
            new_index.add(np.array(embeddings))
            
            logger.info(f"Index rebuilt successfully: {new_index.ntotal} vectors")
            return new_index
            
        except Exception as e:
            logger.error(f"Error rebuilding index: {e}")
            return None
    
    def delete_single_file(self, filename: str, model=None) -> Dict[str, Any]:
        """Delete a single file and update system"""
        logger.info(f"[DELETE] Starting deletion of: {filename}")
        
        # Load current system state
        index, chunks, metadata, files_info = self.load_system_data()
        
        # Validate file exists
        if filename not in files_info:
            available_files = list(files_info.keys())
            return {
                "success": False,
                "error": f"File '{filename}' not found",
                "available_files": available_files
            }
        
        try:
            # Get file info
            file_info = files_info[filename]
            start_idx = file_info["start_index"]
            end_idx = file_info["end_index"]
            chunks_to_remove = end_idx - start_idx + 1
            
            logger.info(f"File info: {chunks_to_remove} chunks (index {start_idx}-{end_idx})")
            
            # 1. Remove physical file
            file_path = os.path.join(self.upload_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"[OK] Physical file removed: {file_path}")
            
            # 2. Remove chunks and metadata
            new_chunks = []
            new_metadata = []
            
            # Keep chunks before deleted file
            for i in range(start_idx):
                new_chunks.append(chunks[i])
                new_metadata.append(metadata[i])
            
            # Skip deleted file chunks (start_idx to end_idx)
            
            # Keep chunks after deleted file with updated indices
            for i in range(end_idx + 1, len(chunks)):
                new_chunks.append(chunks[i])
                updated_meta = metadata[i].copy()
                updated_meta["chunk_id"] = len(new_chunks) - 1
                new_metadata.append(updated_meta)
            
            # 3. Update file indices
            files_updated = []
            for other_filename, other_info in files_info.items():
                if other_filename != filename:
                    if other_info["start_index"] > end_idx:
                        other_info["start_index"] -= chunks_to_remove
                        other_info["end_index"] -= chunks_to_remove
                        files_updated.append(other_filename)
            
            # 4. Remove file from registry
            del files_info[filename]
            
            # 5. Rebuild index
            new_index = None
            if new_chunks and model:
                new_index = self.rebuild_index(new_chunks, model)
            
            # 6. Save updated data
            save_success = self.save_system_data(new_index, new_chunks, new_metadata, files_info)
            
            result = {
                "success": True,
                "deleted_file": filename,
                "removed_chunks": chunks_to_remove,
                "remaining_files": len(files_info),
                "remaining_chunks": len(new_chunks),
                "files_updated": files_updated,
                "index_rebuilt": new_index is not None,
                "save_success": save_success
            }
            
            logger.info(f"[OK] Deletion successful: {result}")
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Error during deletion: {e}")
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }
    
    def delete_multiple_files(self, filenames: List[str], model=None) -> Dict[str, Any]:
        """Delete multiple files"""
        results = []
        errors = []
        
        for filename in filenames:
            try:
                result = self.delete_single_file(filename, model)
                if result["success"]:
                    results.append({
                        "filename": filename,
                        "status": "success",
                        "removed_chunks": result["removed_chunks"]
                    })
                else:
                    errors.append({
                        "filename": filename,
                        "error": result["error"]
                    })
            except Exception as e:
                errors.append({
                    "filename": filename,
                    "error": str(e)
                })
        
        return {
            "status": "completed",
            "successful_deletions": len(results),
            "failed_deletions": len(errors),
            "results": results,
            "errors": errors
        }
    
    def clear_all_data(self) -> Dict[str, Any]:
        """Clear all data from system"""
        logger.info("[DELETE] Clearing all system data...")
        
        try:
            files_removed = 0
            
            # Remove physical files
            if os.path.exists(self.upload_dir):
                for filename in os.listdir(self.upload_dir):
                    if filename.endswith('.pdf'):
                        os.remove(os.path.join(self.upload_dir, filename))
                        files_removed += 1
            
            # Remove index files
            index_files = [
                self.faiss_index_path,
                self.metadata_path,
                self.files_info_path,
                self.chunks_path
            ]
            
            for file_path in index_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            logger.info(f"[OK] System cleared: {files_removed} files removed")
            
            return {
                "success": True,
                "message": "All data cleared successfully",
                "files_removed": files_removed,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[ERROR] Error clearing system: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        index, chunks, metadata, files_info = self.load_system_data()
        
        return {
            "total_files": len(files_info),
            "total_chunks": len(chunks),
            "index_vectors": index.ntotal if index else 0,
            "metadata_entries": len(metadata),
            "files_list": list(files_info.keys())
        }


# ==================== STANDALONE DELETE SCRIPT ====================

def standalone_delete_tool():
    """Standalone tool untuk delete file tanpa server"""
    import sys
    from sentence_transformers import SentenceTransformer
    
    print("[DELETE] DocNLP Standalone Delete Tool")
    print("=" * 40)
    
    # Initialize
    base_dir = os.path.dirname(os.path.abspath(__file__))
    delete_manager = DeleteManager(base_dir)
    
    # Load model for index rebuilding
    try:
        print("Loading model...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[OK] Model loaded")
    except Exception as e:
        print(f"[WARNING] Model loading failed: {e}")
        model = None
    
    # Get current files
    stats = delete_manager.get_system_stats()
    print(f"\nCurrent system stats:")
    print(f"  Files: {stats['total_files']}")
    print(f"  Chunks: {stats['total_chunks']}")
    print(f"  Index vectors: {stats['index_vectors']}")
    
    if not stats['files_list']:
        print("\n[ERROR] No files to delete")
        return
    
    print(f"\nAvailable files:")
    for i, filename in enumerate(stats['files_list'], 1):
        print(f"  {i}. {filename}")
    
    # Interactive delete
    if len(sys.argv) > 1:
        # Command line argument
        filename = " ".join(sys.argv[1:])
        print(f"\nDeleting from command line: {filename}")
    else:
        # Interactive selection
        try:
            choice = input(f"\nEnter file number to delete (1-{len(stats['files_list'])}), or 'all' to clear everything: ")
            
            if choice.lower() == 'all':
                confirm = input("Are you sure you want to delete ALL files? (yes/no): ")
                if confirm.lower() == 'yes':
                    result = delete_manager.clear_all_data()
                    if result['success']:
                        print(f"[OK] All data cleared: {result['files_removed']} files removed")
                    else:
                        print(f"[ERROR] Error: {result['error']}")
                return
            
            file_idx = int(choice) - 1
            if 0 <= file_idx < len(stats['files_list']):
                filename = stats['files_list'][file_idx]
            else:
                print("[ERROR] Invalid selection")
                return
                
        except (ValueError, KeyboardInterrupt):
            print("\n[ERROR] Operation cancelled")
            return
    
    # Perform delete
    print(f"\n[DELETE] Deleting: {filename}")
    result = delete_manager.delete_single_file(filename, model)
    
    if result['success']:
        print(f"[OK] Delete successful!")
        print(f"  Removed chunks: {result['removed_chunks']}")
        print(f"  Remaining files: {result['remaining_files']}")
        print(f"  Remaining chunks: {result['remaining_chunks']}")
        print(f"  Index rebuilt: {result['index_rebuilt']}")
    else:
        print(f"[ERROR] Delete failed: {result['error']}")


if __name__ == "__main__":
    standalone_delete_tool()
