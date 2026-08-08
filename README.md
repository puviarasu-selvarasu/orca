# 🐋 O.R.C.A. – On-device Resource-Constrained Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django 4.2](https://img.shields.io/badge/django-4.2-green.svg)](https://www.djangoproject.com/)

**O.R.C.A.** is a sovereign, offline-first AI assistant that runs entirely on your local machine. It combines a local LLM, a personal knowledge base (RAG), an autonomous code builder, predictive analytics, and OCR file upload – all without any cloud dependencies.

> **"A Jarvis for your laptop, built on an 8GB budget."**

---

## ✨ Features

### 🧠 Core Intelligence
- **100% Offline LLM** – Uses a quantized Phi‑3 or Qwen model running on your CPU.
- **Persistent Chat** – Threaded conversations saved to SQLite.
- **RAG (Retrieval-Augmented Generation)** – Semantic search over your personal documents, notes, and codebases using ChromaDB (<50ms retrieval).

### 🔧 Builder Mode (The "Hands")
- **Instant Mock Plan** – Generate a boilerplate project in <1 second.
- **AI‑Generated Plan** – Custom project structures for Django, Laravel, and Spring Boot (background, non‑blocking).
- **Secure Sandbox** – Writes files and executes commands in an isolated directory with AST security scanning.
- **Multi‑language Support** – Python, PHP (Laravel), Java (Spring Boot).

### 📊 The Oracle (Predictive + Strategic Analytics)
- **System Health Forecasts** – Predicts CPU/RAM spikes using Scikit‑learn.
- **Knowledge Gap Detection** – Analyzes your chat history to suggest topics for study.
- **Strategic Advice** – Actionable recommendations like "Close Chrome to speed up this build."

### 📎 The Scanner (OCR + File Upload)
- Upload images, PDFs, or text files – O.R.C.A. extracts text via local Tesseract OCR.
- Auto‑populates the chat input with the extracted text (truncated to fit the LLM context window).

### 🎨 Tactical UI
- Dark‑mode, cinematic interface with scanlines, glass‑morphism, and neon accents.
- Custom modals for delete and approve actions – no ugly browser popups.
- Live CPU/RAM metrics with color‑coded warnings.

---

## 🛠️ Tech Stack

| Category | Tools |
| :--- | :--- |
| **Backend** | Django 4.2, Python 3.11 |
| **Frontend** | Alpine.js, Tailwind CSS (custom dark theme) |
| **Local LLM** | llama-cpp-python, Phi‑3 / TinyLlama GGUF |
| **Vector DB** | ChromaDB, sentence-transformers |
| **Data Science** | Scikit‑learn, Pandas, NumPy |
| **OCR** | Tesseract, pytesseract, pdfplumber |
| **Security** | AST scanning, sandboxed subprocess |
| **Deployment** | (Optional) Cloudflare Tunnel, Render (thin‑client) |

---

## 🚀 Getting Started

### Prerequisites
- **Windows 11** (or Linux/macOS with minor adjustments)
- **Python 3.11+**
- **Git**
- **~8 GB RAM** (recommended)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/puviarasu-selvarasu/orca.git
cd orca

Create and activate a virtual environment

bash
python -m venv venv_orca
source venv_orca/bin/activate   # On Windows: venv_orca\Scripts\activate


Install dependencies

bash
pip install -r requirements.txt


Download the LLM model (Phi‑3 mini Q4_K_M)

bash
curl -L -o models/phi-3-mini-4k-instruct-q4_K_M.gguf https://huggingface.co/bartowski/Phi-3-mini-4k-instruct-GGUF/resolve/main/Phi-3-mini-4k-instruct-Q4_K_M.gguf


Create the .env file

bash
cp .env.example .env
# Edit .env with your SECRET_KEY and other settings

Run migrations and create a superuser

bash
python manage.py migrate
python manage.py createsuperuser


Start the server

bash
python manage.py runserver

Access the dashboard at http://127.0.0.1:8000/ and log in.

How to Use
Chat – Type your questions or commands. O.R.C.A. will respond using its local LLM and your knowledge base.

Upload Documents – Drop your PDFs, notes, or code into the knowledge/ folder and run the ingestion script (python manage.py ingest).

Build Software – Describe a project (e.g., "Build me a Laravel blog"). Click "Generate Plan" to see a template, or "AI Plan" for a custom structure. Approve and execute to let O.R.C.A. write the code.

Get Strategic Advice – Visit /api/oracle/advice/ or integrate it into your workflow.

OCR Upload – In the Builder console, click "Upload Requirements" and select an image or PDF to extract text.

Acknowledgements
llama-cpp-python for CPU inference.

ChromaDB for vector search.

Tesseract for OCR.

Django, Alpine.js, and all other open‑source libraries used.


Future Roadmap
Voice Interface – Local STT/TTS using Whisper.cpp and Piper.

Vision – Local image analysis with Moondream or Florence‑2 (via Sandbox).

Self‑Healing Loop – Autonomous error correction for generated code.

Mobile App – React Native companion for phone access.

Built by Puviarasu-Selvarasu – feel free to reach out for questions or collaborations.