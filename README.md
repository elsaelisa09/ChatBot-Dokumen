# DocumentAI - Sistem Tanya Jawab Dokumen Berbasis AI

![DocumentAI](https://img.shields.io/badge/DocumentAI-v1.0.0-blue)
![React](https://img.shields.io/badge/React-18.3.1-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.5-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)

Sistem tanya jawab dokumen yang menggunakan AI untuk menganalisis dan menjawab pertanyaan tentang dokumen PDF dengan teknologi hybrid retrieval (BM25 + FAISS semantic search).

## ✨ Features

### Frontend (React + TypeScript)

- 💬 **Chat Interface** - Interface chat yang modern dan responsif
- 📁 **File Upload** - Upload file PDF dengan drag & drop
- 🎤 **Voice Input** - Input suara untuk pertanyaan
- ⚡ **Quick Questions** - Tombol pertanyaan cepat yang sudah disiapkan
- 🎨 **Modern UI** - Menggunakan Tailwind CSS + Shadcn/ui components
- 📱 **Responsive Design** - Optimized untuk desktop dan mobile

### Backend (FastAPI + Python)

- 🤖 **AI-Powered Q&A** - Menggunakan DeepSeek Chat V3 untuk menjawab pertanyaan
- 🔍 **Hybrid Retrieval** - Kombinasi BM25 dan FAISS semantic search
- 🎯 **Smart Question Detection** - Deteksi otomatis jenis pertanyaan
- 📊 **RESTful API** - API yang lengkap dan well-documented
- 🌐 **CORS Support** - Support untuk frontend integration
- 📁 **File Management** - Upload, list, dan delete file PDF

### Question Types Support

- 📋 **Rangkuman Dokumen** - Merangkum seluruh isi dokumen
- 📅 **Informasi Tanggal** - Mencari tanggal penting dalam dokumen
- 🏠 **Luas & Lokasi Properti** - Informasi properti dalam dokumen
- 🌳 **Area Rambah** - Informasi area rambah
- 📜 **Isi Pasal** - Rangkuman pasal tertentu
- ❓ **Free Questions** - Pertanyaan bebas dengan AI

## 🚀 Quick Start

### Opsi 1: One-Click Setup (Recommended)

**Windows:**

```bash
start-dev.bat
```

**Linux/Mac:**

```bash
chmod +x start-dev.sh
./start-dev.sh
```

Script ini akan otomatis:

- Setup Python virtual environment
- Install semua dependencies (Python + Node.js)
- Download model yang diperlukan
- Start backend dan frontend secara bersamaan

### Opsi 2: Manual Setup

#### Prerequisites

- Python 3.8+
- Node.js 16+
- npm atau yarn

#### Backend Setup

```bash
cd backend

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Start FastAPI server
python main.py
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 📁 Project Structure

```
DocumentAI/
├── backend/                # FastAPI Backend
│   ├── main.py            # FastAPI application
│   ├── ask.py             # Core Q&A logic
│   ├── extract_text.py    # PDF text extraction
│   ├── semantic_chunker.py # Document chunking
│   ├── build_index.py     # FAISS index builder
│   ├── requirements.txt   # Python dependencies
│   ├── .env              # Configuration
│   ├── start.bat         # Windows startup script
│   ├── start.sh          # Linux/Mac startup script
│   └── pdf/              # PDF files directory
│
├── frontend/              # React Frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── lib/          # Utilities & API client
│   │   ├── hooks/        # Custom hooks
│   │   └── pages/        # Page components
│   ├── package.json      # Node.js dependencies
│   └── vite.config.ts    # Vite configuration
│
├── start-dev.bat         # Windows dev startup
├── start-dev.sh          # Linux/Mac dev startup
└── README.md             # This file
```

## 🌐 Access Points

Setelah menjalankan aplikasi:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## 📖 Usage Guide

### 1. Persiapan Dokumen

Sebelum bisa bertanya, pastikan dokumen sudah diproses:

```bash
cd backend

# Extract text dari PDF
python extract_text.py

# Buat chunks dokumen
python semantic_chunker.py

# Build FAISS index
python build_index.py
```

Atau copy file `doc_index.faiss` dan `doc_chunks.pkl` yang sudah ada.

### 2. Upload Dokumen Baru

- Gunakan interface frontend untuk upload PDF
- Atau gunakan API endpoint `/upload`
- Setelah upload, jalankan script build index untuk memproses

### 3. Bertanya

Gunakan salah satu format pertanyaan ini:

#### Quick Questions

- **Rangkum dokumen**: "Rangkum dokumen [nama]"
- **Tanggal perjanjian**: "Kapan perjanjian dibuat untuk dokumen [nama]"
- **Lahan Properti**: "Luas lahan dan lokasi lahan properti untuk dokumen [nama]"
- **Area Rambah**: "Luas dan lokasi area rambah untuk dokumen [nama]"
- **Rangkum isi pasal**: "Rangkum isi pasal [nomor] untuk dokumen [nama]"

#### Contoh Pertanyaan

```
Rangkum dokumen Akarsana Fujiati
Kapan perjanjian dibuat untuk dokumen Balijan Nugroho
Luas lahan properti untuk dokumen Clara Widiastuti
Rangkum isi pasal 3 untuk dokumen Galak Ardianto
```

## 🔧 Configuration

### Backend Configuration (.env)

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

### Frontend Configuration

Edit `src/lib/api.ts` untuk mengubah backend URL jika diperlukan:

```typescript
const API_BASE_URL = "http://localhost:8000";
```

## 🛠️ Development

### Adding New Question Types

1. **Backend** - Edit `ask.py`:

```python
def detect_question_type(question):
    q = question.lower()
    if any(k in q for k in ["new_keyword"]):
        return "new_type"
    # ... existing code
```

2. **Frontend** - Edit `QuickQuestions.tsx`:

```typescript
const quickQuestions = [
  {
    label: "New Question Type",
    template: "New question template [nama]",
  },
  // ... existing questions
];
```

### Custom Retrieval Strategy

Edit `hybrid_retrieval()` in `ask.py`:

```python
# Adjust weighting: current 40% BM25 + 60% FAISS
combined_scores = 0.4 * bm25_scores_norm + 0.6 * faiss_scores_norm
```

## 🐛 Troubleshooting

### Common Issues

1. **Backend tidak bisa start**

   - Check Python version (3.8+)
   - Pastikan semua dependencies terinstall
   - Check port 8000 tidak digunakan aplikasi lain

2. **Frontend tidak bisa connect ke backend**

   - Pastikan backend running di http://localhost:8000
   - Check CORS configuration
   - Verify API_BASE_URL di frontend

3. **spaCy model error**

   ```bash
   python -m spacy download en_core_web_sm
   ```

4. **No documents found**

   - Build document index terlebih dahulu
   - Check file PDF ada di folder `backend/pdf/`

5. **API key errors**
   - Verify OpenAI/OpenRouter API key di `.env`
   - Check internet connection

### Debug Mode

- Set `DEBUG=True` di backend `.env`
- Check browser console untuk frontend errors
- Check backend console untuk detailed logs

## 📄 API Documentation

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

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **DeepSeek Chat V3** - AI model untuk Q&A
- **FastAPI** - Modern Python web framework
- **React** - Frontend framework
- **FAISS** - Similarity search library
- **Sentence Transformers** - Embedding models
- **spaCy** - NLP library
- **Tailwind CSS** - CSS framework
- **Shadcn/ui** - UI components

---

**Happy Document Analyzing! 📚🤖**
