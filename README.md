# CravingAI — Multimodal RAG Restaurant Recommendation System

A production-grade, highly interactive AI restaurant and dish recommendation engine (similar to Zomato & Swiggy combined with a ChatGPT-style conversational backend). Powered by hybrid text + image search queries, a FAISS vector database, AWS S3 image storage, and AWS Bedrock (Claude 3.5 Sonnet + Titan Multimodal Embeddings).

## Project Structure

```
├── backend/                  # FastAPI Web Server
│   ├── api/                  # API Routers (upload, recommend, chat)
│   ├── config.py             # Config & Pydantic settings loading
│   ├── db/                   # FAISS Database management & Auto-seeding
│   ├── main.py               # Application entrypoint & static mounting
│   ├── models/               # Request & Response Pydantic schemas
│   ├── services/             # S3 storage, Bedrock Titan, and Claude LLM
│   ├── utils/                # Logging & latency utilities
│   └── requirements.txt      # Python dependencies (NumPy, Pillow, Boto3, FAISS)
├── frontend/                 # Glassmorphic Dark-Mode UI (served by FastAPI)
│   ├── index.html            # Main markup page
│   ├── style.css             # Glassmorphism styling & animations
│   └── app.js                # Frontend controller & API integrations
├── data/                     # Local data storage for fallbacks & cached images
├── vector_db/                # Saved FAISS index files
├── Dockerfile                # Production Docker deployment
└── docker-compose.yml        # Multi-container volume-mapped orchestration
```

---

## Features

- **Multimodal Hybrid Search**: Search for food using text keywords or uploaded images (drag & drop). Adjust the relative influence of text vs. image embeddings via an interactive weight slider.
- **RAG Latency Dashboard**: Real-time performance stats showing API processing latency and FAISS vector retrieval times.
- **Conversational recommendation Assistant (Chat)**: Converse with the AI to refine restaurant listings or discuss diet plans. Retrieved matches are displayed side-by-side with chat history.
- **Automatic Fallback Modes**: Automatic seed execution if the FAISS index is empty on startup. Automatically switches to local disk fallback for S3 storage and mock embeddings if AWS credentials are not configured.

---

## Setup & Running Guide

### Method A: Local execution (FastAPI + Embedded Frontend)

1. **Clone and Configure Env**:
   Copy the `.env.example` file to `.env` and fill in your AWS credentials:
   ```powershell
   copy .env.example .env
   ```

2. **Initialize Python Environment**:
   Ensure you have Python 3.12+ installed. Run:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

3. **Start the server**:
   ```powershell
   python -m uvicorn backend.main:app --port 8000 --reload
   ```

4. **Access the App**:
   - Go to **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** to interact with the visual web interface.
   - Go to **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** to inspect the OpenAPI docs.

---

### Method B: Containerized Execution (Docker Compose)

To launch the system in an isolated container mapping persistent volumes for image caching and search indices:
```bash
docker compose up --build
```
Once initialized, visit **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**.
