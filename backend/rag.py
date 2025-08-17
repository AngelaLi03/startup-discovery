import numpy as np
import json
import os
from pathlib import Path
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv
import faiss
from scipy.stats import norm
from scipy.special import expit

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
    
    def _build_background_distribution(self) -> tuple[float, float]:
        """
        Build background (negative) similarity distribution.
        Uses random query embeddings to establish baseline similarity distribution.
        """
        if not self.is_index_loaded():
            return 0.0, 1.0
        
        # Generate random query-like embeddings to establish baseline
        num_samples = min(100, len(self.metadata) * 2)  # Reasonable sample size
        random_embeddings = np.random.randn(num_samples, 1536).astype('float32')
        
        # Normalize to unit vectors (like real embeddings)
        random_embeddings = random_embeddings / np.linalg.norm(random_embeddings, axis=1, keepdims=True)
        
        # Search with random embeddings to get background scores
        background_scores = []
        for i in range(0, num_samples, 10):  # Process in batches
            batch = random_embeddings[i:i+10]
            if len(batch) > 0:
                scores, _ = self.index.search(batch, 5)  # Get top 5 for each random query
                background_scores.extend(scores.flatten())
        
        # Calculate background distribution parameters
        mu_0 = float(np.mean(background_scores))
        sigma_0 = float(np.std(background_scores))
        
        print(f"📊 Background distribution: μ₀={mu_0:.4f}, σ₀={sigma_0:.4f}")
        return mu_0, sigma_0
    
    def _calibrate_score(self, raw_score: float, mu_0: float, sigma_0: float) -> float:
        """
        Calibrate raw similarity score using z-score normalization and logistic squashing.
        
        Args:
            raw_score: Raw FAISS similarity score
            mu_0: Background distribution mean
            sigma_0: Background distribution standard deviation
            
        Returns:
            Calibrated score in [0, 100] range
        """
        # Step 2: Calculate z-score
        z_score = (raw_score - mu_0) / sigma_0 if sigma_0 > 0 else 0
        
        # Step 3: Create much more dramatic score variation
        # Use aggressive scaling to create better separation
        
        # Scale down z-score dramatically since they're very high
        scaled_z = z_score / 15.0  # Scale down by factor of 15
        
        if scaled_z > 2.5:  # Very high relevance
            calibrated_score = 90 + (scaled_z - 2.5) * 4.0  # 90-100 range
        elif scaled_z > 2.0:  # High relevance
            calibrated_score = 80 + (scaled_z - 2.0) * 20.0  # 80-90 range
        elif scaled_z > 1.5:  # Good relevance
            calibrated_score = 65 + (scaled_z - 1.5) * 30.0  # 65-80 range
        elif scaled_z > 1.0:  # Moderate relevance
            calibrated_score = 45 + (scaled_z - 1.0) * 40.0  # 45-65 range
        elif scaled_z > 0.5:  # Low relevance
            calibrated_score = 20 + (scaled_z - 0.5) * 50.0  # 20-45 range
        else:  # Very low relevance
            calibrated_score = max(0, scaled_z * 40.0)  # 0-20 range
        
        return max(0.0, min(100.0, calibrated_score))
    
    def _get_score_interpretation(self, calibrated_score: float) -> tuple[str, str]:
        """
        Get score interpretation based on calibrated score.
        
        Args:
            calibrated_score: Score in [0, 100] range
            
        Returns:
            Tuple of (label, color_emoji)
        """
        if calibrated_score >= 95:
            return "Perfect Match", "🟢"
        elif calibrated_score >= 85:
            return "Excellent Match", "🟢"
        elif calibrated_score >= 70:
            return "Very Good Match", "🟢"
        elif calibrated_score >= 55:
            return "Good Match", "🟡"
        elif calibrated_score >= 40:
            return "Fair Match", "🟡"
        elif calibrated_score >= 25:
            return "Weak Match", "🟠"
        else:
            return "Poor Match", "🔴"
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a single text."""
        response = self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return np.array(response.data[0].embedding)
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Perform semantic search for startups with globally calibrated scoring.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of startup data with calibrated similarity scores
        """
        if not self.is_index_loaded():
            raise Exception("Index not loaded. Run ingest.py first.")
        
        # Step 1: Build background distribution for calibration
        print("🔧 Building background similarity distribution...")
        mu_0, sigma_0 = self._build_background_distribution()
        
        # Get query embedding
        query_embedding = self.get_embedding(query)
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        
        # Search in FAISS index
        scores, indices = self.index.search(query_embedding, top_k)
        
        # Ensure scores and indices are Python native types
        scores = scores.tolist() if hasattr(scores, 'tolist') else scores
        indices = indices.tolist() if hasattr(indices, 'tolist') else indices
        
        # Format results with calibrated scoring
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.metadata):
                startup_data = self.metadata[idx].copy()
                
                # Step 2 & 3: Calibrate the raw score
                raw_score = float(score)
                calibrated_score = self._calibrate_score(raw_score, mu_0, sigma_0)
                
                # Get score interpretation
                score_label, score_color = self._get_score_interpretation(calibrated_score)
                
                # Store both raw and calibrated scores (ensure Python native types)
                startup_data["similarity_score"] = float(raw_score)
                startup_data["similarity_percentage"] = float(round(calibrated_score, 1))
                startup_data["similarity_label"] = str(score_label)
                startup_data["similarity_color"] = str(score_color)
                startup_data["calibration_info"] = {
                    "z_score": float(round((raw_score - mu_0) / sigma_0, 3) if sigma_0 > 0 else 0),
                    "background_mean": float(round(mu_0, 4)),
                    "background_std": float(round(sigma_0, 4))
                }
                startup_data["rank"] = int(i + 1)
                
                # Create explanation of why this startup matched
                startup_text = f"{startup_data['name']} {startup_data['description']} {startup_data['industry']} {startup_data['location']}".lower()
                query_terms = query.lower().split()
                matching_terms = [term for term in query_terms if term in startup_text]
                
                if matching_terms:
                    startup_data["match_reason"] = str(f"Matched on: {', '.join(set(matching_terms))}")
                else:
                    startup_data["match_reason"] = str("Semantic similarity match")
                
                # Ensure all numeric fields are Python native types
                startup_data["id"] = int(startup_data["id"])
                startup_data["founded"] = int(startup_data["founded"])
                startup_data["team_size"] = int(startup_data["team_size"])
                
                # Final safety check: convert any remaining numpy types
                for key, value in startup_data.items():
                    if hasattr(value, 'item'):  # numpy scalar
                        startup_data[key] = value.item()
                    elif hasattr(value, 'tolist'):  # numpy array
                        startup_data[key] = value.tolist()
                
                results.append(startup_data)
        
        print(f"🎯 Calibrated {len(results)} results using background distribution")
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
