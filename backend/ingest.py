import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv
import faiss
import pickle

# Load environment variables
load_dotenv()

class StartupIngester:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.index_dir = Path("index")
        self.data_dir = Path("data")
        self.index_dir.mkdir(exist_ok=True)
        
    def load_startup_data(self) -> pd.DataFrame:
        """Load startup data from CSV file."""
        csv_path = self.data_dir / "startups.csv"
        if not csv_path.exists():
            # Create sample data if file doesn't exist
            self._create_sample_data()
        
        df = pd.read_csv(csv_path)
        return df
    
    def _create_sample_data(self):
        """Create sample startup data for testing."""
        sample_data = [
            {
                "name": "TechFlow",
                "description": "AI-powered workflow automation platform for enterprise teams",
                "industry": "Enterprise Software",
                "funding": "$15M Series A",
                "location": "San Francisco, CA",
                "founded": 2021,
                "team_size": 45
            },
            {
                "name": "GreenEnergy",
                "description": "Renewable energy solutions for residential and commercial buildings",
                "industry": "Clean Energy",
                "funding": "$8M Seed",
                "location": "Austin, TX",
                "founded": 2022,
                "team_size": 23
            },
            {
                "name": "HealthAI",
                "description": "Machine learning platform for early disease detection and diagnosis",
                "industry": "Healthcare",
                "funding": "$25M Series B",
                "location": "Boston, MA",
                "founded": 2020,
                "team_size": 67
            },
            {
                "name": "EduTech",
                "description": "Personalized learning platform using adaptive algorithms",
                "industry": "Education",
                "funding": "$12M Series A",
                "location": "Seattle, WA",
                "founded": 2021,
                "team_size": 34
            },
            {
                "name": "FinTechPro",
                "description": "Blockchain-based payment processing and financial services",
                "industry": "Financial Services",
                "funding": "$30M Series C",
                "location": "New York, NY",
                "founded": 2019,
                "team_size": 89
            }
        ]
        
        df = pd.DataFrame(sample_data)
        df.to_csv(self.data_dir / "startups.csv", index=False)
        print(f"Created sample data with {len(sample_data)} startups")
    
    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for a list of texts using OpenAI API."""
        embeddings = []
        for text in texts:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            embeddings.append(response.data[0].embedding)
        return np.array(embeddings)
    
    def create_search_text(self, row: pd.Series) -> str:
        """Create searchable text from startup data."""
        return f"{row['name']} {row['description']} {row['industry']} {row['location']}"
    
    def ingest(self):
        """Main ingestion process."""
        print("Loading startup data...")
        df = self.load_startup_data()
        
        print("Creating searchable text...")
        search_texts = [self.create_search_text(row) for _, row in df.iterrows()]
        
        print("Generating embeddings...")
        embeddings = self.get_embeddings(search_texts)
        
        print("Creating FAISS index...")
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        index.add(embeddings.astype('float32'))
        
        print("Saving index and metadata...")
        # Save FAISS index
        faiss.write_index(index, str(self.index_dir / "faiss.index"))
        
        # Save metadata
        metadata = []
        for i, (_, row) in enumerate(df.iterrows()):
            metadata.append({
                "id": i,
                "name": row["name"],
                "description": row["description"],
                "industry": row["industry"],
                "funding": row["funding"],
                "location": row["location"],
                "founded": int(row["founded"]),
                "team_size": int(row["team_size"])
            })
        
        with open(self.index_dir / "meta.jsonl", "w") as f:
            for item in metadata:
                f.write(json.dumps(item) + "\n")
        
        print(f"✅ Successfully ingested {len(df)} startups")
        print(f"📁 Index saved to: {self.index_dir / 'faiss.index'}")
        print(f"📄 Metadata saved to: {self.index_dir / 'meta.jsonl'}")

if __name__ == "__main__":
    ingester = StartupIngester()
    ingester.ingest()
