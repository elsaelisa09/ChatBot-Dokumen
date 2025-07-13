import asyncio
import os
import threading
import time
from pathlib import Path
from typing import Dict, List
import logging
from datetime import datetime
import json

# Import existing modules
from semantic_chunker import split_into_chunks, load_pdf_text
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class TaskStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class BackgroundTaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.model = None
        self.index = None
        self.chunks = []
        self.metadatas = []
        self.load_existing_data()
        
    def load_existing_data(self):
        """Load existing FAISS index and chunks if they exist"""
        try:
            if os.path.exists("doc_index.faiss") and os.path.exists("doc_chunks.pkl"):
                self.index = faiss.read_index("doc_index.faiss")
                with open("doc_chunks.pkl", "rb") as f:
                    data = pickle.load(f)
                    self.chunks = data["chunks"]
                    self.metadatas = data["metadatas"]
                logger.info(f"Loaded existing index with {len(self.chunks)} chunks")
            else:
                # Initialize empty index
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                embedding_dim = self.model.get_sentence_embedding_dimension()
                self.index = faiss.IndexFlatL2(embedding_dim)
                self.chunks = []
                self.metadatas = []
                logger.info("Initialized empty index")
        except Exception as e:
            logger.error(f"Error loading existing data: {e}")
            # Fallback to empty index
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            embedding_dim = self.model.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatL2(embedding_dim)
            self.chunks = []
            self.metadatas = []
    
    def create_task(self, task_id: str, task_type: str, file_path: str) -> str:
        """Create a new background task"""
        self.tasks[task_id] = {
            "id": task_id,
            "type": task_type,
            "status": TaskStatus.PENDING,
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "created_at": datetime.now().isoformat(),
            "progress": 0,
            "message": "Task created",
            "error": None
        }
        
        # Start processing in background thread
        thread = threading.Thread(target=self._process_task, args=(task_id,))
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Dict:
        """Get status of a specific task"""
        return self.tasks.get(task_id, {"status": "not_found"})
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Remove tasks older than max_age_hours"""
        try:
            current_time = datetime.now()
            to_remove = []
            
            for task_id, task in self.tasks.items():
                created_at = datetime.fromisoformat(task["created_at"])
                age_hours = (current_time - created_at).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.tasks[task_id]
                logger.info(f"Cleaned up old task: {task_id}")
                
            return len(to_remove)
        except Exception as e:
            logger.error(f"Error cleaning up tasks: {e}")
            return 0
    
    def _process_task(self, task_id: str):
        """Process a single file indexing task"""
        try:
            task = self.tasks[task_id]
            file_path = task["file_path"]
            filename = task["filename"]
            
            # Update status
            task["status"] = TaskStatus.PROCESSING
            task["progress"] = 10
            task["message"] = "Extracting text from PDF..."
            
            # Extract text
            text = load_pdf_text(file_path)
            if not text:
                raise Exception("Failed to extract text from PDF")
            
            task["progress"] = 30
            task["message"] = "Creating semantic chunks..."
            
            # Create chunks
            new_chunks, new_metadatas = split_into_chunks(text, filename)
            if not new_chunks:
                raise Exception("No chunks created from document")
            
            task["progress"] = 60
            task["message"] = "Generating embeddings..."
            
            # Load model if not already loaded
            if self.model is None:
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
            
            # Generate embeddings for new chunks
            embeddings = self.model.encode(new_chunks, show_progress_bar=False)
            embeddings = np.array(embeddings).astype("float32")
            
            task["progress"] = 80
            task["message"] = "Updating index..."
            
            # Add to existing data
            self.chunks.extend(new_chunks)
            self.metadatas.extend(new_metadatas)
            
            # Add embeddings to index
            self.index.add(embeddings)
            
            task["progress"] = 95
            task["message"] = "Saving index..."
            
            # Save updated index and chunks
            faiss.write_index(self.index, "doc_index.faiss")
            with open("doc_chunks.pkl", "wb") as f:
                pickle.dump({
                    "chunks": self.chunks,
                    "metadatas": self.metadatas
                }, f)
            
            # Complete task
            task["status"] = TaskStatus.COMPLETED
            task["progress"] = 100
            task["message"] = f"Successfully indexed {len(new_chunks)} chunks from {filename}"
            task["completed_at"] = datetime.now().isoformat()
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            # Mark task as failed
            self.tasks[task_id]["status"] = TaskStatus.FAILED
            self.tasks[task_id]["error"] = str(e)
            self.tasks[task_id]["message"] = f"Failed: {str(e)}"
            logger.error(f"Task {task_id} failed: {e}")
    
    def get_all_tasks(self) -> List[Dict]:
        """Get all active tasks"""
        return list(self.tasks.values())
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Remove old completed/failed tasks"""
        current_time = datetime.now()
        to_remove = []
        
        for task_id, task in self.tasks.items():
            created_at = datetime.fromisoformat(task["created_at"])
            age_hours = (current_time - created_at).total_seconds() / 3600
            
            if age_hours > max_age_hours and task["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old tasks")

# Global task manager instance
task_manager = BackgroundTaskManager()
