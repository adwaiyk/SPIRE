from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import os

# Import our custom Data Structures & AI Models
from core.bloom_filter import ChemicalBloomFilter
from core.vp_tree import VPTree
from data.pdb_parser import AlphaFoldParser
from ml.gnn_ranker import AIRanker

app = FastAPI(title="SPIRE Engine API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows the Windows Next.js frontend to talk to the WSL backend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("--- INITIALIZING SPIRE ENGINE v2.0 ---")

# 1. Gatekeeper: Unit 6 Bloom Filter
pocket_filter = ChemicalBloomFilter(expected_items=100, false_positive_rate=0.01)
pocket_filter.add("HAS_SULPHUR")

# 2. Boot up AI Models
print("Booting up AlphaFold Pipeline & PyTorch GNN...")
af_parser = AlphaFoldParser()
ai_ranker = AIRanker()

# 3. Ingest Real Biological Data
# P04637: p53 Tumor Suppressor | P02144: Myoglobin | P00734: Prothrombin
db_ids = ["P04637", "P02144", "P00734"]
db_points = []
pocket_coords_db = {} # We must store the raw atoms so the GNN can graph them later

# Step 6 Flex: AlphaMissense Mock Database
# DeepMind flagged p53 (P04637) as highly sensitive to mutation.
alphamissense_db = {
    "P04637": True,  # HIGHLY CONSERVED - Trigger Warning!
    "P02144": False,
    "P00734": False
}

for pid in db_ids:
    raw_file = af_parser.fetch_alphafold_structure(pid)
    if not raw_file:
        continue
        
    clean_file = af_parser.filter_by_plddt(raw_file, pid)
    coords = af_parser.run_fpocket(clean_file)
    vec = af_parser.generate_vp_feature_vector(coords)
    
    db_points.append(vec)
    pocket_coords_db[pid] = coords
    print(f" -> {pid} Indexed. PCA Vector: [{vec[0]:.1f}, {vec[1]:.1f}, {vec[2]:.1f}]")

# 4. Build Precision Navigator: Unit 5 VP-Tree
vp_tree = VPTree(np.array(db_points), db_ids)
print("--- SPIRE ENGINE ONLINE ---")

# --- API ROUTES ---
class SearchQuery(BaseModel):
    required_property: str
    query_vector: list[float] 

@app.post("/search")
def run_spire_pipeline(query: SearchQuery):
    # Step 2 Pipeline check: O(1) Chemical Rejection
    if not pocket_filter.check(query.required_property):
        return {"match_found": False, "reason": "Failed Bloom Filter chemical check."}
    
    # Step 4 Pipeline check: O(log N) Spatial Nearest Neighbor Search
    query_np = np.array(query.query_vector)
    best_pocket, distance = vp_tree.search_nearest(query_np)
    
    if distance > 200.0:
        return {"match_found": False, "reason": "No structurally similar pocket found."}
        
    # Step 5 Pipeline check: PyTorch GNN Ranking
    candidate_data = [{
        "id": best_pocket,
        "coords": pocket_coords_db[best_pocket]
    }]
    
    # Run the graph analysis
    ranked_results = ai_ranker.rank_pockets(candidate_data)
    top_match = ranked_results[0]
    
    return {
        "match_found": True,
        "protein_id": top_match["id"],
        "metric_distance": float(distance),
        "ai_score": float(top_match["ai_binding_score"]),
        "alphamissense_warning": alphamissense_db.get(top_match["id"], False),
        "message": f"Successfully matched via VP-Tree. GNN Binding Affinity: {top_match['ai_binding_score']:.2%}"
    }