from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # <-- NEW IMPORT
import numpy as np
import pickle
import os
import hashlib

from core.geo_hash import GeometricHashTable
from ml.gnn_ranker import AIRanker
from data.pdb_parser import AlphaFoldParser

app = FastAPI(title="SPIRE Engine API", version="4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# <-- NEW: Serve the local PDB files directly to the frontend! -->
os.makedirs("data/raw", exist_ok=True)
app.mount("/static", StaticFiles(directory="data/raw"), name="static")

print("=========================================")
print("      BOOTING SPIRE DATABASE ENGINE      ")
print("=========================================")

index_path = "data/index/spire_master.pkl"
if not os.path.exists(index_path):
    raise FileNotFoundError("Database index not found! Run scripts/build_index.py first.")

with open(index_path, "rb") as f:
    db_package = pickle.load(f)

vp_tree = db_package["vp_tree"]
pocket_filter = db_package["bloom_filter"]
pocket_coords_db = db_package["raw_coords"]

geo_hash = GeometricHashTable(bin_size=20.0)
for pid, coords in pocket_coords_db.items():
    centered = coords - np.mean(coords, axis=0)
    cov_matrix = np.cov(centered, rowvar=False)
    eigenvalues, _ = np.linalg.eigh(cov_matrix)
    vec = np.sort(eigenvalues)[::-1]
    geo_hash.insert(pid, vec)

ai_ranker = AIRanker()
af_parser = AlphaFoldParser() # Needed to process user uploads

print(f"--- SPIRE ONLINE: {db_package['indexed_count']} Pockets Indexed ---")
print("=========================================")

@app.post("/upload_search")
async def search_uploaded_pdb(
    file: UploadFile = File(...),
    required_property: str = Form(...)
):
    # Step 1: Bloom Filter - O(1) Chemical Rejection
    if not pocket_filter.check(required_property):
        return {"match_found": False, "reason": "Failed Bloom Filter chemical check."}

    # Save the uploaded file temporarily
    temp_path = f"data/raw/temp_query_{file.filename}"
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())

    # Extract geometry from the uploaded file
    try:
        # Assuming the user uploads a pre-cut pocket. If it's a whole protein, 
        # af_parser.run_fpocket(temp_path) would be used here instead.
        raw_atoms = af_parser._extract_coords(temp_path, "query")
        query_np = af_parser.generate_vp_feature_vector(raw_atoms)
    except Exception as e:
        return {"match_found": False, "reason": f"Failed to parse PDB file: {str(e)}"}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Step 2: Geometric Hashing - O(1) Candidate Identification
    candidates = geo_hash.get_candidates(query_np)
    if not candidates:
        return {"match_found": False, "reason": "Geometric Hashing found zero rotation-invariant candidates for this uploaded topology."}

    # Step 3: VP-Tree - O(log N) Precision Navigator
    best_pocket, distance = vp_tree.search_nearest(query_np)
    
    if best_pocket not in candidates or distance > 150.0:
        return {"match_found": False, "reason": "No structurally identical pocket found within metric bounds."}

    # Step 4: GNN - AI Judge Ranking
    candidate_data = [{"id": best_pocket, "coords": pocket_coords_db[best_pocket]}]
    ranked_results = ai_ranker.rank_pockets(candidate_data)
    top_match = ranked_results[0]
    
    # Step 5: Dynamic AlphaMissense Simulator
    # In production, this queries the 200GB DeepMind CSV. Here we simulate consistency via hashing.
    hash_val = int(hashlib.md5(top_match["id"].encode()).hexdigest(), 16)
    is_hotspot = hash_val % 3 == 0 # ~33% chance to flag as a critical mutation hotspot

    return {
        "match_found": True,
        "protein_id": top_match["id"],
        "metric_distance": float(distance),
        "ai_score": float(top_match["ai_binding_score"]),
        "alphamissense_warning": is_hotspot,
        "message": f"Pipeline Success. Top Match verified via VP-Tree."
    }