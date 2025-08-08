from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn

from models import SearchResult, AskResponse
from rag import RAGPipeline

app = FastAPI(title="Startup Discovery API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG pipeline
rag_pipeline = RAGPipeline()

@app.get("/")
async def root():
    return {"message": "Startup Discovery API - Use /search or /ask endpoints"}

@app.get("/search", response_model=List[SearchResult])
async def search_startups(q: str = Query(..., description="Search query")):
    """
    Semantic search for startups based on natural language query.
    """
    try:
        results = rag_pipeline.search(q)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/ask", response_model=AskResponse)
async def ask_about_startups(q: str = Query(..., description="Question about startups")):
    """
    Get LLM-powered answer about startups based on retrieved data.
    """
    try:
        answer = rag_pipeline.ask(q)
        return AskResponse(question=q, answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Q&A failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "index_loaded": rag_pipeline.is_index_loaded()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
