# Startup Discovery — RAG Semantic Search + LLM Q&A

A retrieval-augmented generation (RAG) service that ingests startup data, indexes it with embeddings, and provides semantic search and LLM-powered Q&A capabilities.

## Features

- **Semantic Search**: Find startups using natural language queries
- **LLM Q&A**: Get AI-powered answers about startups based on retrieved data
- **FAISS Indexing**: Fast similarity search using vector embeddings
- **OpenAI Integration**: Uses OpenAI API for embeddings and chat completions
- **Real-time Data**: Automatically fetches latest startup data from Crunchbase API
- **Scheduled Updates**: Background scheduler keeps data fresh every 12 hours
- **Smart Caching**: Only re-embeds changed startup data to save costs

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
   cp env.example .env
   # Add your OpenAI API key and Crunchbase API key to .env
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
- `GET /health` - Health check with sync status

## Crunchbase Integration

The application automatically fetches real-time startup data from Crunchbase API:

- **Automatic Updates**: Runs every 12 hours to keep data fresh
- **Smart Sync**: Only fetches changed/updated startups
- **Rate Limiting**: Respects API limits with automatic backoff
- **Fallback Data**: Uses sample data if API is unavailable
- **Content Hashing**: Tracks changes to minimize re-embedding costs

### Setup Crunchbase API

1. Get your API key from [Crunchbase Developer Portal](https://data.crunchbase.com/docs/using-the-api)
2. Add to `.env`: `CRUNCHBASE_API_KEY=your_key_here`
3. Run `python ingest.py` to fetch initial data

## Tech Stack

- **Backend**: Python, FastAPI, FAISS, OpenAI API
- **Data Processing**: pandas, numpy
- **Data Sources**: Crunchbase API, Web scraping fallback
- **Scheduling**: APScheduler for background updates
- **Frontend**: React, TypeScript (optional)

