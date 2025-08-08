# Startup Discovery — RAG Semantic Search + LLM Q&A

A retrieval-augmented generation (RAG) service that ingests startup data, indexes it with embeddings, and provides semantic search and LLM-powered Q&A capabilities.

## Features

- **Semantic Search**: Find startups using natural language queries
- **LLM Q&A**: Get AI-powered answers about startups based on retrieved data
- **FAISS Indexing**: Fast similarity search using vector embeddings
- **OpenAI Integration**: Uses OpenAI API for embeddings and chat completions

## Architecture

```
startup-discovery/
├── backend/           # FastAPI backend with RAG functionality
│   ├── app.py        # Main FastAPI application
│   ├── ingest.py     # Data ingestion and FAISS indexing
│   ├── rag.py        # RAG pipeline implementation
│   ├── models.py     # Pydantic models and data structures
│   └── data/         # Startup dataset
└── frontend/         # React frontend (optional)
```

## Quick Start

1. **Setup Environment**:
   ```bash
   cd backend
   cp .env.example .env
   # Add your OpenAI API key to .env
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ingest Data**:
   ```bash
   python ingest.py
   ```

4. **Run Server**:
   ```bash
   uvicorn app:app --reload
   ```

## API Endpoints

- `GET /search?q=query` - Semantic search for startups
- `GET /ask?q=query` - LLM-powered Q&A about startups

## Tech Stack

- **Backend**: Python, FastAPI, FAISS, OpenAI API
- **Data Processing**: pandas, numpy
- **Frontend**: React, TypeScript (optional)

