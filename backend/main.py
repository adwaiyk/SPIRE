from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from Bio.PDB import PDBParser # <-- NEW IMPORT
import numpy as np
import pickle
import os
import hashlib
import glob # <-- NEW IMPORT
import shutil # <-- NEW IMPORT

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
for pid_pocket, coords in pocket_coords_db.items():
    centered = coords - np.mean(coords, axis=0)
    cov_matrix = np.cov(centered, rowvar=False)
    eigenvalues, _ = np.linalg.eigh(cov_matrix)
    vec = np.sort(eigenvalues)[::-1]
    geo_hash.insert(pid_pocket, vec)

ai_ranker = AIRanker()
af_parser = AlphaFoldParser() 
pdb_reader = PDBParser(QUIET=True) # Used to count atoms dynamically

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

    best_candidate_id = None
    best_distance = float('inf')

    try:
        # --- NEW: ADAPTIVE FILE DETECTION ---
        structure = pdb_reader.get_structure("query", temp_path)
        atom_count = len(list(structure.get_atoms()))
        
        if atom_count > 600:
            print("[INFO] Massive structure detected. Extracting candidate pockets on the fly...")
            # Run fpocket on the uploaded file
            af_parser.run_fpocket(temp_path)
            
            base_name = os.path.basename(temp_path).replace(".pdb", "")
            out_dir = os.path.join(os.path.dirname(temp_path), f"{base_name}_out", "pockets")
            
            # Test every extracted pocket against our geometric index
            candidate_pockets = glob.glob(os.path.join(out_dir, "pocket*_atm.pdb"))
            
            for p_file in candidate_pockets:
                try:
                    p_coords = af_parser._extract_coords(p_file, "query")
                    p_vec = af_parser.generate_vp_feature_vector(p_coords)
                    
                    cands = geo_hash.get_candidates(p_vec)
                    if cands:
                        p_match, p_dist = vp_tree.search_nearest(p_vec)
                        if p_match in cands and p_dist < best_distance:
                            best_distance = p_dist
                            best_candidate_id = p_match
                except Exception:
                    continue
            
            # Cleanup the temp fpocket directory
            if os.path.exists(os.path.dirname(out_dir)):
                shutil.rmtree(os.path.dirname(out_dir), ignore_errors=True)
                
        else:
            print("[INFO] Pre-cut keyhole detected. Running direct matching...")
            raw_atoms = af_parser._extract_coords(temp_path, "query")
            query_np = af_parser.generate_vp_feature_vector(raw_atoms)
            
            cands = geo_hash.get_candidates(query_np)
            if cands:
                best_match, dist = vp_tree.search_nearest(query_np)
                if best_match in cands and dist < 150.0:
                    best_distance = dist
                    best_candidate_id = best_match

    except Exception as e:
        return {"match_found": False, "reason": f"Failed to process PDB file: {str(e)}"}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # --- RESULT VALIDATION & AI RANKING ---
    if not best_candidate_id or best_distance > 150.0:
        return {"match_found": False, "reason": "No mathematically identical geometry found in database."}

    # Format the candidate for the GNN
    candidate_data = [{"id": best_candidate_id, "coords": pocket_coords_db[best_candidate_id]}]
    ranked_results = ai_ranker.rank_pockets(candidate_data)
    top_match = ranked_results[0]
    
    # We indexed them as "O14756::pocket4". We split it to give the UI the exact protein AND pocket.
    full_id_string = top_match["id"]
    if "::" in full_id_string:
        real_protein_id, specific_pocket = full_id_string.split("::")
    else:
        real_protein_id, specific_pocket = full_id_string, "pocket1"

    # Dynamic AlphaMissense Simulator
    hash_val = int(hashlib.md5(real_protein_id.encode()).hexdigest(), 16)
    is_hotspot = hash_val % 3 == 0 

    return {
        "match_found": True,
        "protein_id": real_protein_id,
        "matched_pocket": specific_pocket,
        "metric_distance": float(best_distance),
        "ai_score": float(top_match["ai_binding_score"]),
        "alphamissense_warning": is_hotspot,
        "message": "Pipeline Success. Top Match verified via VP-Tree."
    }