from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from typing import List

# Import our Unit 5 & Unit 6 Data Structures
from core.bloom_filter import ChemicalBloomFilter
from core.geo_hash import GeometricHashTable
from core.vp_tree import VPTree

app = FastAPI(title="SPIRE Engine API", version="1.0")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL DATA STRUCTURES ---
# In a real app, these load from a saved file. We are initializing them in memory for now.
print("Initializing SPIRE Data Structures...")

# 1. Initialize Bloom Filter
pocket_filter = ChemicalBloomFilter(expected_items=100, false_positive_rate=0.01)
pocket_filter.add("HYDROPHOBIC")
pocket_filter.add("HAS_SULPHUR")

# 2. Initialize Geometric Hash Table
geo_hash = GeometricHashTable(bin_size=2.0)
target_pocket = np.array([[0., 0., 0.], [5., 0., 0.], [0., 5., 0.], [2., 2., 5.], [1., 1., 1.]])
geo_hash.insert_pocket("Target_COVID_Spike", target_pocket)

# 3. Initialize VP-Tree
db_points = np.array([
    [1.0, 2.0, 3.0],   # Liver_Protein_A
    [10.0, 10.0, 10.0],# Target_COVID_Spike (Vectorized representation)
    [5.0, 5.0, 5.0]    # Brain_Protein_C
])
db_ids = ["Liver_Protein_A", "Target_COVID_Spike", "Brain_Protein_C"]
vp_tree = VPTree(db_points, db_ids)

print("SPIRE Engine Ready.")

# --- API MODELS ---
# This defines the JSON structure Next.js must send to us
class SearchQuery(BaseModel):
    required_property: str
    query_vector: List[float] # e.g., [9.5, 10.2, 9.8]

# --- API ROUTES ---
@app.get("/")
def health_check():
    return {"status": "SPIRE API is online", "ds_loaded": True}

@app.post("/search")
def run_spire_pipeline(query: SearchQuery):
    """
    The main search pipeline linking Unit 5 and Unit 6 structures.
    """
    # STEP 1: Bloom Filter check
    if not pocket_filter.check(query.required_property):
        return {"match_found": False, "reason": "Failed Bloom Filter chemical check. Property missing."}
    
    # STEP 2 & 3: VP-Tree Nearest Neighbor Search
    # (In a full app, we'd query GeoHash first to get candidates, then VP-Tree to rank them. 
    # For this API endpoint, we'll demonstrate the exact metric search)
    query_np = np.array(query.query_vector)
    best_pocket, distance = vp_tree.search_nearest(query_np)
    
    # We set a threshold. If the distance is too large, it's not a real match.
    if distance > 5.0:
        return {"match_found": False, "reason": "No structurally similar pocket found within metric threshold."}
        
    return {
        "match_found": True,
        "protein_id": best_pocket,
        "metric_distance": float(distance),
        "message": f"Successfully matched {best_pocket} in O(log N) time!"
    }