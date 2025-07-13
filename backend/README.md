# DocumentAI Backend

FastAPI backend untuk sistem tanya jawab dokumen menggunakan AI.

## Features

- 🤖 AI-powered document Q&A menggunakan DeepSeek Chat V3
- 📁 Upload file PDF
- 🔍 Hybrid retrieval (BM25 + FAISS semantic search)
- 🎯 Question type detection (rangkuman, tanggal, pasal, dll)
- 📊 RESTful API dengan FastAPI
- 🌐 CORS support untuk frontend integration

## Quick Start

### Windows

```bash
start.bat
```

### Linux/Mac

```bash
chmod +x start.sh
./start.sh
```

### Manual Setup

1. **Buat virtual environment:**

```bash
python -m venv venv
```

2. **Aktifkan virtual environment:**

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Download spaCy model:**

```bash
python -m spacy download en_core_web_sm
```

5. **Build document index (jika belum ada):**

```bash
python extract_text.py
python semantic_chunker.py
python build_index.py
```

6. **Start server:**

```bash
python main.py
```

Server akan berjalan di `http://localhost:8000`

## API Endpoints

### Health Check

```http
GET /health
```

### Ask Question

```http
POST /ask
Content-Type: application/json

{
  "question": "Rangkum dokumen Akarsana Fujiati",
  "top_k": 5
}
```

### Upload File

```http
POST /upload
Content-Type: multipart/form-data

file: <PDF file>
```

### List Files

```http
GET /files
```

### Delete File

```http
DELETE /files/{filename}
```

### Get Document Owners

```http
GET /owners
```

## Configuration

Edit `.env` file untuk konfigurasi:

```env
# API Configuration
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
MODEL_NAME=deepseek/deepseek-chat-v3-0324:free

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# File Upload Configuration
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=pdf

# CORS Configuration
FRONTEND_URL=http://localhost:5173
```

## File Structure

```
backend/
├── main.py              # FastAPI app
├── ask.py               # Core Q&A logic
├── extract_text.py      # PDF text extraction
├── semantic_chunker.py  # Document chunking
├── build_index.py       # FAISS index builder
├── requirements.txt     # Dependencies
├── .env                 # Configuration
├── start.bat           # Windows startup script
├── start.sh            # Linux/Mac startup script
├── pdf/                # PDF files directory
├── doc_index.faiss     # FAISS index (generated)
└── doc_chunks.pkl      # Document chunks (generated)
```

## Development

### Add New Question Types

Edit `detect_question_type()` function in `ask.py`:

```python
def detect_question_type(question):
    q = question.lower()
    if any(k in q for k in ["new_keyword"]):
        return "new_type"
    # ... existing code
```

Then add handling in `ask_question()` function.

### Custom Retrieval Strategy

Modify `hybrid_retrieval()` function to adjust BM25 vs FAISS weighting:

```python
# Current: 40% BM25 + 60% FAISS
combined_scores = 0.4 * bm25_scores_norm + 0.6 * faiss_scores_norm
```

## Troubleshooting

### Common Issues

1. **Import errors:** Install missing packages with `pip install <package>`
2. **spaCy model not found:** Run `python -m spacy download en_core_web_sm`
3. **No documents found:** Build index with the provided scripts
4. **API connection failed:** Check internet connection and API key

### Debug Mode

Set `DEBUG=True` in `.env` for detailed logging.

### Logs

Check console output for detailed error messages and processing steps.

## API Documentation

Interactive API docs available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
