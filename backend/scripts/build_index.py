import os
import pickle
import numpy as np
import sys
import urllib.request
import json

# Add the parent directory to the path so we can import our core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bloom_filter import ChemicalBloomFilter
from core.vp_tree import VPTree
from data.pdb_parser import AlphaFoldParser

def fetch_top_100_human_proteins():
    """Dynamically fetches the top 100 reviewed Human Protein IDs from UniProt."""
    print("[INFO] Fetching 100 Human Protein IDs from UniProt API...")
    url = "https://rest.uniprot.org/uniprotkb/search?query=(reviewed:true)%20AND%20(organism_id:9606)&size=100&fields=accession"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Python/SPIRE'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            # Extract just the IDs (e.g., 'P04637')
            return [result['primaryAccession'] for result in data['results']]
    except Exception as e:
        print(f"[ERROR] Failed to fetch from UniProt: {e}")
        # Fallback list just in case you have no wifi during your demo
        return ["P04637", "P02144", "P00734", "P15056", "P01112", "P35968"]

def build_spire_database():
    print("=========================================")
    print("   SPIRE OFFLINE INDEX BUILDER v1.0      ")
    print("=========================================")

    af_parser = AlphaFoldParser()
    pocket_filter = ChemicalBloomFilter(expected_items=10000, false_positive_rate=0.01)
    
    pocket_filter.add("HAS_SULPHUR")
    pocket_filter.add("HYDROPHOBIC")
    pocket_filter.add("KINASE_LIKE")

    # Fetch our 100 target proteins
    database_ids = fetch_top_100_human_proteins()
    
    db_points = []
    pocket_coords_db = {}
    successful_ids = []

    print(f"\n[INFO] Starting batch processing of {len(database_ids)} AlphaFold structures...")
    print("[INFO] This will take a few minutes as fpocket calculates the 3D Voronoi cavities.\n")
    
    for idx, pid in enumerate(database_ids):
        print(f"Processing [{idx+1}/{len(database_ids)}]: {pid}")
        
        raw_file = af_parser.fetch_alphafold_structure(pid)
        if not raw_file:
            continue
            
        clean_file = af_parser.filter_by_plddt(raw_file, pid)
        coords = af_parser.run_fpocket(clean_file)
        
        # Skip proteins that are too flat to have a real pocket
        if len(coords) < 10:
            print(f"  -> [SKIP] No distinct pocket found.")
            continue
            
        vec = af_parser.generate_vp_feature_vector(coords)
        
        db_points.append(vec)
        pocket_coords_db[pid] = coords
        successful_ids.append(pid)
        
        print(f"  -> [SUCCESS] PCA Vector: [{vec[0]:.1f}, {vec[1]:.1f}, {vec[2]:.1f}]")

    print("\n=========================================")
    print("[INFO] Building Data Structures...")
    
    vp_tree = VPTree(np.array(db_points), successful_ids)

    print("[INFO] Saving SPIRE Database to disk...")
    os.makedirs("data/index", exist_ok=True)
    
    db_package = {
        "vp_tree": vp_tree,
        "bloom_filter": pocket_filter,
        "raw_coords": pocket_coords_db,
        "indexed_count": len(successful_ids)
    }

    with open("data/index/spire_master.pkl", "wb") as f:
        pickle.dump(db_package, f)

    print(f"\n[SUCCESS] SPIRE Database built!")
    print(f"Successfully extracted deep pockets from {len(successful_ids)} out of {len(database_ids)} proteins.")
    print("Saved to 'data/index/spire_master.pkl'")
    print("=========================================")

if __name__ == "__main__":
    build_spire_database()