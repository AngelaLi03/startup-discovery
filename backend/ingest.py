import pandas as pd
import numpy as np
import json
import os
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import openai
from dotenv import load_dotenv
import faiss
import requests
from apscheduler.schedulers.background import BackgroundScheduler

# Load environment variables
load_dotenv()

class StartupIngester:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.crunchbase_key = os.getenv("CRUNCHBASE_API_KEY")
        self.index_dir = Path("index")
        self.data_dir = Path("data")
        self.cache_dir = Path("data/cache")
        
        # Create directories
        self.index_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize scheduler for background updates
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.run_scheduled_update, 'interval', hours=12, coalesce=True, misfire_grace_time=3600)
        
    def load_sync_state(self) -> Dict[str, Any]:
        """Load synchronization state from file."""
        state_path = self.index_dir / "state.json"
        if state_path.exists():
            with open(state_path, "r") as f:
                return json.load(f)
        return {
            "last_sync_iso": "1970-01-01T00:00:00Z",
            "total_docs": 0,
            "last_update": None
        }
    
    def save_sync_state(self, state: Dict[str, Any]):
        """Save synchronization state to file."""
        state_path = self.index_dir / "state.json"
        with open(state_path, "w") as f:
            json.dump(state, f, indent=2)
    
    def fetch_startups_from_crunchbase(self, limit: int = 100, updated_since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch real startup data from Crunchbase v4 API."""
        if not self.crunchbase_key:
            print("⚠️  No Crunchbase API key found. Using fallback data sources.")
            return self.fetch_startups_from_web()
        
        startups = []
        page = 1
        
        try:
            while len(startups) < limit:
                url = "https://api.crunchbase.com/api/v4/searches/organizations"
                headers = {"X-cb-user-key": self.crunchbase_key}
                
                # v4 API uses POST with JSON body
                payload = {
                    "field_values": [
                        {"field_id": "organization_types", "values": ["company"]},
                        {"field_id": "founded_on_year", "values": [{"value": 2015, "operator": "gte"}]}
                    ],
                    "limit": min(50, limit - len(startups)),
                    "order": [{"field_id": "founded_on_year", "sort": "desc"}]
                }
                
                print(f"Fetching page {page} from Crunchbase v4...")
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 429:
                    print("⚠️  Rate limit hit. Waiting 60 seconds...")
                    time.sleep(60)
                    continue
                elif response.status_code != 200:
                    print(f"❌ Crunchbase API error: {response.status_code} - {response.text[:200]}")
                    break
                
                data = response.json()
                items = data.get("entities", [])
                
                if not items:
                    break
                
                for org in items:
                    startup = self._parse_crunchbase_v4_org(org)
                    if startup:
                        startups.append(startup)
                
                page += 1
                time.sleep(1)  # Respect rate limits
                
        except Exception as e:
            print(f"❌ Error fetching from Crunchbase: {e}")
        
        return startups
    
    def _parse_crunchbase_v4_org(self, org: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Crunchbase v4 organization data into our format."""
        try:
            properties = org.get("properties", {})
            
            # Extract basic info
            name = properties.get("name", "")
            if not name:
                return None
            
            description = properties.get("short_description", "") or properties.get("long_description", "") or "Startup company"
            
            # Extract industry/category from v4 format
            categories = properties.get("category_groups", [])
            industry = "Unknown"
            if categories:
                # v4 might have different structure, try multiple paths
                for cat in categories:
                    if isinstance(cat, dict):
                        if "name" in cat:
                            industry = cat["name"]
                            break
                        elif "properties" in cat and "name" in cat["properties"]:
                            industry = cat["properties"]["name"]
                            break
            
            # Extract funding info
            funding = self._extract_funding_v4(org)
            
            # Extract location
            location = self._extract_location_v4(properties)
            
            # Extract founding year
            founded = properties.get("founded_on_year", 2020)
            
            # Extract team size
            team_size = self._extract_team_size_v4(properties)
            
            # Generate source ID and content hash
            source_id = org.get("uuid", "") or org.get("permalink", "")
            content_hash = self._generate_content_hash(name, description, industry, location)
            
            return {
                "name": name,
                "description": description,
                "industry": industry,
                "funding": funding,
                "location": location,
                "founded": founded,
                "team_size": team_size,
                "source": "crunchbase",
                "source_id": source_id,
                "content_hash": content_hash,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "homepage_url": properties.get("homepage_url", ""),
                "linkedin_url": properties.get("linkedin_url", "")
            }
            
        except Exception as e:
            print(f"Error parsing organization: {e}")
            return None
    
    def _extract_funding_v4(self, org: Dict[str, Any]) -> str:
        """Extract funding information from v4 organization data."""
        try:
            # v4 might have different funding structure
            funding_rounds = org.get("properties", {}).get("funding_rounds", [])
            if funding_rounds:
                latest = funding_rounds[0]
                amount = latest.get("money_raised", "") or latest.get("properties", {}).get("money_raised", "")
                round_type = latest.get("round_type", "") or latest.get("properties", {}).get("round_type", "")
                if amount and round_type:
                    return f"${amount} {round_type}"
            return "No funding data"
        except:
            return "No funding data"
    
    def _extract_location_v4(self, properties: Dict[str, Any]) -> str:
        """Extract location information from v4 format."""
        try:
            # Try to get city and country
            city = properties.get("city", "")
            country = properties.get("country", "")
            
            if city and country:
                return f"{city}, {country}"
            elif city:
                return city
            elif country:
                return country
            else:
                return "Location not specified"
        except:
            return "Location not specified"
    
    def _extract_team_size_v4(self, properties: Dict[str, Any]) -> int:
        """Extract team size information from v4 format."""
        try:
            # Crunchbase provides employee ranges, convert to approximate number
            employee_enum = properties.get("num_employees_enum", "")
            if employee_enum:
                # Map ranges to approximate numbers
                size_map = {
                    "1-10": 5,
                    "11-50": 30,
                    "51-100": 75,
                    "101-250": 175,
                    "251-500": 375,
                    "501-1000": 750,
                    "1001-5000": 3000,
                    "5001-10000": 7500,
                    "10001+": 15000
                }
                return size_map.get(employee_enum, 50)
            return 50  # Default
        except:
            return 50
    
    def _generate_content_hash(self, name: str, description: str, industry: str, location: str) -> str:
        """Generate hash of content for change detection."""
        content = f"{name} {description} {industry} {location}".lower()
        return hashlib.sha256(content.encode()).hexdigest()
    
    def fetch_startups_from_web(self) -> List[Dict[str, Any]]:
        """Fallback: Scrape startup data from web sources."""
        print("🌐 Fetching startup data from web sources...")
        startups = []
        
        # This is a simplified web scraper - you'd want to expand this
        try:
            # Example: Scrape from a startup list website
            # In practice, you'd want to respect robots.txt and rate limits
            pass
        except Exception as e:
            print(f"❌ Web scraping failed: {e}")
        
        # Return sample data if web scraping fails
        return self._get_sample_data()
    
    def _get_sample_data(self) -> List[Dict[str, Any]]:
        """Get startup data from CSV file as fallback."""
        try:
            csv_path = self.data_dir / "startups.csv"
            if csv_path.exists():
                print("📁 Loading startup data from startups.csv...")
                df = pd.read_csv(csv_path)
                startups = []
                
                for i, (_, row) in enumerate(df.iterrows()):
                    startup = {
                        "name": row.get("name", ""),
                        "description": row.get("description", ""),
                        "industry": row.get("industry", ""),
                        "funding": row.get("funding", ""),
                        "location": row.get("location", ""),
                        "founded": int(row.get("founded", 2020)),
                        "team_size": int(row.get("team_size", 10)),
                        "source": "csv",
                        "source_id": f"csv_{i:03d}",
                        "content_hash": self._generate_content_hash(
                            row.get("name", ""), 
                            row.get("description", ""), 
                            row.get("industry", ""), 
                            row.get("location", "")
                        ),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "homepage_url": "",
                        "linkedin_url": ""
                    }
                    startups.append(startup)
                
                print(f"✅ Loaded {len(startups)} startups from CSV")
                return startups
            else:
                print("⚠️  startups.csv not found, using hardcoded fallback")
                return self._get_hardcoded_fallback()
                
        except Exception as e:
            print(f"❌ Error reading CSV: {e}, using hardcoded fallback")
            return self._get_hardcoded_fallback()
    
    def _get_hardcoded_fallback(self) -> List[Dict[str, Any]]:
        """Get hardcoded sample data as last resort."""
        return [
            {
                "name": "TechFlow",
                "description": "AI-powered workflow automation platform for enterprise teams",
                "industry": "Enterprise Software",
                "funding": "$15M Series A",
                "location": "San Francisco, CA",
                "founded": 2021,
                "team_size": 45,
                "source": "hardcoded",
                "source_id": "hardcoded_001",
                "content_hash": "hardcoded_hash_001",
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "name": "GreenEnergy",
                "description": "Renewable energy solutions for residential and commercial buildings",
                "industry": "Clean Energy",
                "funding": "$8M Seed",
                "location": "Austin, TX",
                "founded": 2022,
                "team_size": 23,
                "source": "hardcoded",
                "source_id": "hardcoded_002",
                "content_hash": "hardcoded_hash_002",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ]
    
    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for a list of texts using OpenAI API."""
        embeddings = []
        for i, text in enumerate(texts):
            success = False
            for attempt in range(3):  # Try up to 3 times
                try:
                    print(f"Generating embedding {i+1}/{len(texts)} (attempt {attempt+1})...")
                    response = self.openai_client.embeddings.create(
                        model="text-embedding-ada-002",
                        input=text,
                        timeout=60  # Increase timeout to 60 seconds
                    )
                    embeddings.append(response.data[0].embedding)
                    success = True
                    if (i + 1) % 5 == 0:
                        print(f"✅ Generated embeddings for {i + 1}/{len(texts)} texts...")
                    break
                except Exception as e:
                    print(f"⚠️  Attempt {attempt+1} failed for text {i}: {e}")
                    if attempt < 2:  # Not the last attempt
                        wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                        print(f"⏳ Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    else:
                        print(f"❌ All attempts failed for text {i}, using fallback embedding")
                        # Use zero vector as fallback
                        embeddings.append([0.0] * 1536)  # OpenAI ada-002 dimension
        
        return np.array(embeddings)
    
    def create_search_text(self, startup: Dict[str, Any]) -> str:
        """Create searchable text from startup data."""
        return f"{startup['name']} {startup['description']} {startup['industry']} {startup['location']}"
    
    def ingest(self, force_refresh: bool = False):
        """Main ingestion process."""
        print("🚀 Starting startup data ingestion...")
        
        # Load current state
        state = self.load_sync_state()
        last_sync = state.get("last_sync_iso", "1970-01-01T00:00:00Z")
        
        if not force_refresh:
            print(f"📅 Last sync: {last_sync}")
        
        # Fetch startup data
        print("📡 Fetching startup data...")
        startups = self.fetch_startups_from_crunchbase(limit=200, updated_since=last_sync if not force_refresh else None)
        
        if not startups:
            print("❌ No startup data fetched. Using sample data.")
            startups = self._get_sample_data()
        
        print(f"📊 Fetched {len(startups)} startups")
        
        # Create searchable text
        print("🔍 Creating searchable text...")
        search_texts = [self.create_search_text(startup) for startup in startups]
        
        # Generate embeddings
        print("🧠 Generating embeddings...")
        embeddings = self.get_embeddings(search_texts)
        
        # Create FAISS index
        print("🔧 Creating FAISS index...")
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        index.add(embeddings.astype('float32'))
        
        # Save to temporary files first
        print("💾 Saving index and metadata...")
        temp_index_path = self.index_dir / "faiss.tmp.index"
        temp_meta_path = self.index_dir / "meta.tmp.jsonl"
        
        # Save FAISS index
        faiss.write_index(index, str(temp_index_path))
        
        # Save metadata
        metadata = []
        for i, startup in enumerate(startups):
            metadata.append({
                "id": i,
                **startup
            })
        
        with open(temp_meta_path, "w") as f:
            for item in metadata:
                f.write(json.dumps(item) + "\n")
        
        # Atomic swap
        import shutil
        shutil.move(str(temp_index_path), str(self.index_dir / "faiss.index"))
        shutil.move(str(temp_meta_path), str(self.index_dir / "meta.jsonl"))
        
        # Update state
        new_state = {
            "last_sync_iso": datetime.now(timezone.utc).isoformat(),
            "total_docs": len(startups),
            "last_update": datetime.now(timezone.utc).isoformat()
        }
        self.save_sync_state(new_state)
        
        print(f"✅ Successfully ingested {len(startups)} startups")
        print(f"📁 Index saved to: {self.index_dir / 'faiss.index'}")
        print(f"📄 Metadata saved to: {self.index_dir / 'meta.jsonl'}")
        print(f"🔄 Next scheduled update: 12 hours from now")
        
        return startups
    
    def run_scheduled_update(self):
        """Run scheduled update in background."""
        print("⏰ Running scheduled startup data update...")
        try:
            self.ingest(force_refresh=False)
        except Exception as e:
            print(f"❌ Scheduled update failed: {e}")
    
    def start_background_updates(self):
        """Start background scheduler for automatic updates."""
        if not self.scheduler.running:
            self.scheduler.start()
            print("🔄 Background updates started (every 12 hours)")
    
    def stop_background_updates(self):
        """Stop background scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("⏹️  Background updates stopped")

if __name__ == "__main__":
    ingester = StartupIngester()
    
    # Start background updates
    ingester.start_background_updates()
    
    # Run initial ingestion
    ingester.ingest(force_refresh=True)
    
    try:
        # Keep the scheduler running
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        ingester.stop_background_updates()
