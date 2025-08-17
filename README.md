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
- **Error Handling**: Robust error handling with retry logic and graceful fallbacks

## Architecture

```
startup-discovery/
├── README.md                    # Project documentation
├── backend/                     # FastAPI backend with RAG functionality
│   ├── app.py                  # Main FastAPI application with endpoints
│   ├── ingest.py               # Data ingestion, FAISS indexing, and API integration
│   ├── rag.py                  # RAG pipeline implementation
│   ├── models.py               # Pydantic models and data structures
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example           # Environment variables template
│   ├── data/                   # Startup dataset and fallback data
│   │   └── startups.csv        # Sample startup data (5 companies)
│   └── index/                  # FAISS index and metadata (auto-generated)
│       ├── faiss.index         # Vector embeddings index
│       └── meta.jsonl          # Startup metadata and embeddings
└── frontend/                   # Modern React frontend
    ├── package.json            # Node.js dependencies
    ├── src/                    # React source code
    │   ├── App.tsx            # Main application component
    │   ├── api.ts             # API client for backend communication
    │   └── main.tsx           # React entry point
    ├── index.html             # HTML template
    └── tailwind.config.js     # Tailwind CSS configuration
```

## 🚀 Quick Start

### Backend Setup

1. **Setup environment and run backend server**:
   ```bash
   cd backend
   cp .env.example .env
   pip install -r requirements.txt
   python ingest.py
   uvicorn app:app --reload
   ```

### Frontend Setup

1. **Install Dependencies and run frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
## API Endpoints

- `GET /search?q=query` - Semantic search for startups
- `GET /ask?q=query` - LLM-powered Q&A about startups
- `GET /health` - Health check with sync status

## 🎯 Data Sources & Fallbacks

The system uses a smart fallback strategy to ensure reliable data:

1. **Primary**: Crunchbase API (real-time startup data)
2. **Fallback**: `startups.csv` (5 sample startups with realistic data)
3. **Emergency**: Hardcoded samples (2 basic startups as last resort)

This ensures the application always has data to work with, even when external APIs are unavailable.

## 🔗 Crunchbase Integration

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

### Backend
- **Python 3.8+**: Core runtime
- **FastAPI**: Modern, fast web framework
- **FAISS**: Vector similarity search and clustering
- **OpenAI API**: Text embeddings and LLM completions
- **Pandas & NumPy**: Data processing and manipulation
- **APScheduler**: Background task scheduling

### Frontend
- **React 18**: Modern UI framework
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Vite**: Fast build tool and dev server
- **Axios**: HTTP client for API communication

### Data & Infrastructure
- **Crunchbase API**: Real-time startup data
- **Smart Fallbacks**: CSV data + hardcoded samples
- **Vector Embeddings**: OpenAI text-embedding-ada-002
- **LLM**: GPT-3.5-turbo for Q&A generation
- **Error Handling**: Retry logic with exponential backoff

## Testing & Demo

### Quick Test
1. Start the backend: `cd backend && uvicorn app:app --reload`
2. Start the frontend: `cd frontend && npm run dev`
3. Open your browser and test the search functionality
4. Try asking questions about the available startups

### Sample Queries
- **Search**: "AI companies", "healthcare startups", "fintech companies"
- **Questions**: "What are the most funded startups?", "Which startups are in healthcare?"

## 🔧 Troubleshooting