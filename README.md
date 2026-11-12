# RAG Document Chat & Assistant

A high-performance, modular Retrieval-Augmented Generation (RAG) system built with **FastAPI**, **Streamlit**, **LangChain**, **Qdrant Vector Database**, and **NVIDIA AI Endpoints**.

---

## 📁 Architecture & Folder Structure

```text
rag-doc-chat/
├── backend/                       # 🧠 Core Backend Architecture
│   ├── core/                      # Infrastructure primitives
│   │   ├── config.py              # Pydantic Settings & environment config
│   │   └── retrieval.py           # Qdrant client, collections & vector retriever
│   ├── ingestion/                 # Document ingestion pipeline
│   │   └── ingestion.py           # PDF/TXT/MD loaders, deterministic chunking & indexing
│   ├── api/                       # REST API Layer
│   │   ├── app.py                 # FastAPI endpoints (/health, /chat, /documents)
│   │   └── chain.py               # Two-tier LLM routing, RAG pipeline, Web fallback
│   └── agent/                     # Autonomous capabilities
│       ├── agent.py               # ReAct / Tool-calling agent configuration
│       ├── prompts.py             # Agent system prompts and rules
│       └── tools/                 # Tool implementations
│           ├── document_search.py # Similarity search tool for vector store
│           └── web_search.py      # DDGS web search fallback engine
│
├── frontend/                      # 💻 Streamlit Web Application
│   └── app.py                     # Modern dark-mode UI with persistent chat history
│
├── data/                          # 💾 Application Data (git-ignored)
│   ├── raw/                       # Uploaded user documents (.pdf, .txt, .md)
│   ├── vectorstore/               # Embedded vectors in Qdrant storage
│   ├── chat_history/              # Persisted user conversation sessions
│   └── llm_cache.db               # SQLite cache for LLM responses
│
├── scripts/                       # 🛠️ CLI Utilities & Launchers
│   ├── run_api.py                 # Fast launcher for FastAPI backend
│   ├── ingest.py                  # CLI document ingestion tool
│   ├── chat.py                    # Terminal-based chat interface
│   ├── check_qdrant.py            # Qdrant collection inspector & diagnostics
│   └── view_cache.py              # SQLite LLM cache inspector & purger
│
├── requirements.txt               # Direct pinned dependencies
├── requirements-lock.txt          # Fully frozen dependency lockfile
├── pyproject.toml                 # Package configuration
└── .env                           # Environment configuration & API keys
```

---

## 🚀 Running the Project

### 1. Setup Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ensure `.env` contains your `NVIDIA_API_KEY`:
```env
NVIDIA_API_KEY=nvapi-your-key-here
```

### 2. Start the Backend (FastAPI)
```bash
python scripts/run_api.py
```
* **API Server:** http://localhost:8000
* **Interactive Swagger UI:** http://localhost:8000/docs

### 3. Start the Frontend (Streamlit)
```bash
streamlit run frontend/app.py
```
* **Web UI:** http://localhost:8501

---

## 🐳 Running with Docker

### 1. Configure Environment
Make sure `.env` exists and has your API key:
```bash
cp .env.example .env
# Edit .env and set NVIDIA_API_KEY
```

### 2. Build and Start All Services
```bash
docker compose up --build -d
```

This starts:
- **Qdrant Vector DB:** http://localhost:6333
- **FastAPI Backend:** http://localhost:8000 (Swagger docs at `/docs`)
- **Streamlit Frontend:** http://localhost:8501

### 3. Check Logs & Status
```bash
# View container status and healthchecks
docker compose ps

# Follow logs
docker compose logs -f
```

### 4. Stop Services
```bash
docker compose down
```
*(To also remove the persisted Qdrant volume, pass `-v`: `docker compose down -v`)*
