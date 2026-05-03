import sys
import os
import pickle
import numpy as np
import glob 
import shutil

AMINO_ACID_MAP = {
    'CYS': 'C', 'ASP': 'D', 'SER': 'S', 'GLN': 'Q', 'LYS': 'K',
    'ILE': 'I', 'PRO': 'P', 'THR': 'T', 'PHE': 'F', 'ASN': 'N',
    'GLY': 'G', 'HIS': 'H', 'LEU': 'L', 'ARG': 'R', 'TRP': 'W',
    'ALA': 'A', 'VAL': 'V', 'GLU': 'E', 'TYR': 'Y', 'MET': 'M'
}

# Add the parent directory to the path so we can import our core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ONLY import the original Python classes
from core.bloom_filter import ChemicalBloomFilter
from core.geo_hash import GeometricHashTable
from core.vp_tree import VPTree
from data.pdb_parser import AlphaFoldParser

def fetch_local_proteins():
    """Scans the local data/raw directory for all downloaded protein files."""
    print("[INFO] Scanning local data/raw folder for existing proteins...")
    
    pdb_files = glob.glob("data/raw/*.pdb")
    local_ids = []
    
    for file_path in pdb_files:
        filename = os.path.basename(file_path)
        if "temp" not in filename and "pocket" not in filename:
            pid = filename.replace("_CLEAN.pdb", "").replace("_AF.pdb", "").replace(".pdb", "")
            local_ids.append(pid)
            
    unique_ids = list(set(local_ids))
    print(f"[INFO] Found {len(unique_ids)} unique local proteins to index.")
    return unique_ids

def build_spire_database():
    print("=========================================")
    print("   SPIRE DEEP OFFLINE INDEX BUILDER v2.0 ")
    print("=========================================")

    af_parser = AlphaFoldParser()
    
    # --- INITIALIZE PYTHON DATA STRUCTURES ---
    pocket_filter = ChemicalBloomFilter(expected_items=10000, false_positive_rate=0.01)
    geo_hash = GeometricHashTable() 
    
    pocket_filter.add("HAS_SULPHUR")
    pocket_filter.add("HYDROPHOBIC")
    pocket_filter.add("KINASE_LIKE")

    # Fetch our local proteins
    database_ids = fetch_local_proteins()
    
    db_points = []
    pocket_coords_db = {}
    sequence_db = {}
    successful_ids = []

    # --- Create the Important Proteins directory ---
    imp_folder = "imp_proteins"
    os.makedirs(imp_folder, exist_ok=True)

    print(f"\n[INFO] Starting batch processing of {len(database_ids)} AlphaFold structures...")
    print("[INFO] This will take a few minutes as fpocket calculates the 3D Voronoi cavities.\n")
    
    for idx, pid in enumerate(database_ids):
        print(f"Processing [{idx+1}/{len(database_ids)}]: {pid}")
        
        # We assume the file is already local since we fetched local IDs
        clean_file = f"data/raw/{pid}_CLEAN.pdb"
        
        # Fallback if the clean file doesn't exist but the raw one does
        if not os.path.exists(clean_file):
            raw_file = f"data/raw/{pid}.pdb"
            if os.path.exists(raw_file):
                clean_file = af_parser.filter_by_plddt(raw_file, pid)
            else:
                print(f"  -> [SKIP] File for {pid} not found.")
                continue
        
        current_protein_sequence = ""
        try:
            with open(clean_file, 'r') as f:
                last_res = None
                for line in f:
                    if line.startswith("ATOM"):
                        res_name = line[17:20].strip() # Extract 3-letter code
                        res_num = line[22:26].strip()  # Extract residue ID
                        if res_num != last_res:
                            if res_name in AMINO_ACID_MAP:
                                current_protein_sequence += AMINO_ACID_MAP[res_name]
                            last_res = res_num
        except Exception as e:
            print(f"  -> [WARN] Sequence extraction failed for {pid}: {e}")
            
        # Absolute fallback just in case the file was empty
        if not current_protein_sequence:
            current_protein_sequence = "MKTAY"
            
        sequence_db[pid] = current_protein_sequence

        # --- 2. RUN FPOCKET ---
        _ = af_parser.run_fpocket(clean_file)
        
        # Look for every pocket file fpocket just generated
        pocket_files = glob.glob(f"data/raw/{pid}_CLEAN_out/pockets/pocket*_atm.pdb")
        
        if not pocket_files:
            print(f"  -> [SKIP] No distinct pockets found by fpocket.")
            continue
            
        valid_pocket_found_for_protein = False
            
        for p_file in pocket_files:
            pocket_name = os.path.basename(p_file).replace("_atm.pdb", "")
            coords = af_parser._extract_coords(p_file, "index")
            
            if len(coords) < 10:
                continue 
                
            valid_pocket_found_for_protein = True
            vec = af_parser.generate_vp_feature_vector(coords)
            
            full_id = f"{pid}::{pocket_name}"
            
            # Map the parsed sequence to this pocket ID for the Trie
            # sequence_db[full_id] = current_protein_sequence
            
            # Store data to build the Python VP-Tree later
            db_points.append(vec)
            pocket_coords_db[full_id] = coords
            successful_ids.append(full_id)
            
            # Insert into Python GeoHash
            geo_hash.insert(full_id, vec)
            
            print(f"  -> [INDEXED] {full_id} | PCA Vector: [{vec[0]:.1f}, {vec[1]:.1f}, {vec[2]:.1f}]")

        # --- Copy to imp_proteins if at least one valid pocket was indexed ---
        if valid_pocket_found_for_protein:
            dest_file = os.path.join(imp_folder, f"{pid}_CLEAN.pdb")
            if not os.path.exists(dest_file):
                shutil.copy2(clean_file, dest_file)
                print(f"  -> [SAVED] {pid}_CLEAN.pdb copied to {imp_folder}/")

    print("\n=========================================")
    print("[INFO] Building Data Structures...")
    
    # --- BUILD THE PYTHON VP-TREE ---
    print("[INFO] Building Python VP-Tree...")
    vp_tree = VPTree(np.array(db_points), successful_ids)

    print("[INFO] Saving SPIRE Database to disk...")
    os.makedirs("data/index", exist_ok=True)
    
    db_package = {
        "vp_tree": vp_tree,
        "geo_hash": geo_hash,
        "bloom_filter": pocket_filter,
        "raw_coords": pocket_coords_db,
        "indexed_count": len(successful_ids),
        "sequences": sequence_db,
    }

    with open("data/index/spire_master.pkl", "wb") as f:
        pickle.dump(db_package, f)

    print(f"\n[SUCCESS] SPIRE Database built!")
    print(f"Successfully extracted and indexed {len(successful_ids)} individual pockets.")
    print(f"Successfully verified proteins copied to '{imp_folder}/'")
    print("Saved to 'data/index/spire_master.pkl'")
    print("=========================================")

if __name__ == "__main__":
    build_spire_database()