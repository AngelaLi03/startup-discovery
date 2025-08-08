import numpy as np
import json
import os
from pathlib import Path
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv
import faiss

# Load environment variables
load_dotenv()

class RAGPipeline:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.index_dir = Path("index")
        self.index = None
        self.metadata = []
        self._load_index()
    
    def _load_index(self):
        """Load FAISS index and metadata."""
        try:
            index_path = self.index_dir / "faiss.index"
            meta_path = self.index_dir / "meta.jsonl"
            
            if index_path.exists() and meta_path.exists():
                self.index = faiss.read_index(str(index_path))
                
                # Load metadata
                self.metadata = []
                with open(meta_path, "r") as f:
                    for line in f:
                        self.metadata.append(json.loads(line.strip()))
                
                print(f"✅ Loaded index with {len(self.metadata)} startups")
            else:
                print("⚠️  Index not found. Run ingest.py first.")
        except Exception as e:
            print(f"❌ Error loading index: {e}")
    
    def is_index_loaded(self) -> bool:
        """Check if index is loaded."""
        return self.index is not None and len(self.metadata) > 0
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a single text."""
        response = self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return np.array(response.data[0].embedding)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search for startups.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of startup data with similarity scores
        """
        if not self.is_index_loaded():
            raise Exception("Index not loaded. Run ingest.py first.")
        
        # Get query embedding
        query_embedding = self.get_embedding(query)
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        
        # Search in FAISS index
        scores, indices = self.index.search(query_embedding, top_k)
        
        # Format results
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.metadata):
                startup_data = self.metadata[idx].copy()
                startup_data["similarity_score"] = float(score)
                startup_data["rank"] = i + 1
                results.append(startup_data)
        
        return results
    
    def ask(self, question: str, top_k: int = 3) -> str:
        """
        Get LLM answer based on retrieved startup data.
        
        Args:
            question: User question
            top_k: Number of startups to retrieve for context
            
        Returns:
            LLM-generated answer
        """
        if not self.is_index_loaded():
            raise Exception("Index not loaded. Run ingest.py first.")
        
        # Retrieve relevant startups
        search_results = self.search(question, top_k=top_k)
        
        if not search_results:
            return "I couldn't find any relevant startup information to answer your question."
        
        # Create context from retrieved startups
        context = self._create_context(search_results)
        
        # Generate answer using OpenAI
        prompt = self._create_qa_prompt(question, context)
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions about startups based on the provided information. Be concise and accurate."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def _create_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Create context string from search results."""
        context_parts = []
        for result in search_results:
            context_parts.append(
                f"Startup: {result['name']}\n"
                f"Description: {result['description']}\n"
                f"Industry: {result['industry']}\n"
                f"Location: {result['location']}\n"
                f"Funding: {result['funding']}\n"
                f"Founded: {result['founded']}\n"
                f"Team Size: {result['team_size']}\n"
            )
        return "\n".join(context_parts)
    
    def _create_qa_prompt(self, question: str, context: str) -> str:
        """Create prompt for Q&A."""
        return f"""Based on the following startup information, please answer the question.

Startup Information:
{context}

Question: {question}

Please provide a clear and helpful answer based on the startup information above. If the information doesn't contain enough details to answer the question, please say so."""
