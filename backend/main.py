from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import tempfile
import shutil
from pathlib import Path
import logging
import uuid

# Import fungsi dari ask.py
from ask import ask_question

# Import background task manager
from background_tasks import task_manager, TaskStatus

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DocumentAI Backend",
    description="Backend API untuk sistem tanya jawab dokumen",
    version="1.0.0"
)

# CORS middleware untuk mengizinkan frontend berkomunikasi
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000", 
        "http://localhost:8080",
        "http://localhost:8081",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    answer: str
    status: str

class HealthResponse(BaseModel):
    status: str
    message: str

# Directory untuk file uploads
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    return HealthResponse(
        status="healthy",
        message="DocumentAI Backend is running"
    )

@app.post("/upload", response_model=dict)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload PDF file for processing
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are allowed"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        file_path = UPLOAD_DIR / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File uploaded successfully: {filename}")
        
        return {
            "message": "File uploaded successfully",
            "file_id": file_id,
            "filename": file.filename,
            "file_path": str(file_path)
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )

@app.post("/ask", response_model=QuestionResponse)
async def ask_question_endpoint(request: QuestionRequest):
    """
    Ask question about uploaded documents
    """
    try:
        # Gunakan fungsi ask_question dari ask.py
        answer = ask_question(request.question)
        
        return QuestionResponse(
            answer=answer,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )

@app.get("/files")
async def list_uploaded_files():
    """
    List all uploaded files
    """
    try:
        files = []
        for file_path in UPLOAD_DIR.glob("*.pdf"):
            files.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "upload_time": file_path.stat().st_mtime
            })
        
        return {"files": files}
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing files: {str(e)}"
        )

@app.delete("/files/{filename}")
async def delete_file(filename: str):
    """
    Delete uploaded file
    """
    try:
        file_path = UPLOAD_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        file_path.unlink()
        logger.info(f"File deleted: {filename}")
        
        return {"message": f"File {filename} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting file: {str(e)}"
        )

# Background task endpoints
@app.post("/upload/background")
async def upload_file_background(file: UploadFile = File(...)):
    """
    Upload file and process in background
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are allowed"
            )
        
        # Create task
        task_id = task_manager.create_task(
            task_type="upload",
            description=f"Processing {file.filename}"
        )
        
        # Start background processing
        # This would be implemented with actual background processing
        # For now, we'll simulate it
        task_manager.update_task_status(task_id, TaskStatus.PROCESSING)
        
        # Save file
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        file_path = UPLOAD_DIR / filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update task as completed
        task_manager.update_task_status(task_id, TaskStatus.COMPLETED)
        task_manager.update_task_result(task_id, {
            "file_id": file_id,
            "filename": file.filename,
            "file_path": str(file_path)
        })
        
        return {
            "task_id": task_id,
            "message": "File upload started in background",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error in background upload: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in background upload: {str(e)}"
        )

@app.get("/upload/tasks/{task_id}")
async def get_upload_task_status(task_id: str):
    """
    Get upload task status
    """
    try:
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )
        
        return task
        
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting task status: {str(e)}"
        )

@app.get("/upload/tasks")
async def get_all_upload_tasks():
    """
    Get all upload tasks
    """
    try:
        tasks = task_manager.get_all_tasks()
        return {"tasks": tasks}
        
    except Exception as e:
        logger.error(f"Error getting all tasks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting tasks: {str(e)}"
        )

@app.delete("/upload/cleanup")
async def cleanup_upload_tasks():
    """
    Clean up old upload tasks
    """
    try:
        task_manager.cleanup_old_tasks()
        return {"message": "Old upload tasks cleaned up successfully"}
        
    except Exception as e:
        logger.error(f"Error cleaning up upload tasks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error cleaning up tasks: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    
    print("Starting DocumentAI FastAPI Server...")
    print("Backend ready for document Q&A")
    print("Frontend can connect to: http://localhost:8000")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
