import numpy as np
from collections import defaultdict

class GeometricHashTable:
    """
    Unit 5 Data Structure: Spatial Hashing (Geometric Hashing)
    Provides rotation and translation-invariant 3D matching for protein pockets.
    """
    def __init__(self, bin_size: float = 2.0):
        # The Hash Map: Key = Quantized 3D coordinate (x,y,z), Value = List of Pocket IDs
        self.table = defaultdict(list)
        self.bin_size = bin_size

    def _get_local_basis(self, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray):
        """
        Creates a local 3D coordinate frame (basis) from 3 points.
        This math (Linear Algebra) makes the search rotation-invariant.
        """
        v1 = p2 - p1
        v2 = p3 - p1
        
        # X-axis: pointing from p1 to p2
        x_axis = v1 / np.linalg.norm(v1)
        
        # Z-axis: perpendicular to the triangle surface (Cross Product)
        z_axis = np.cross(x_axis, v2)
        z_norm = np.linalg.norm(z_axis)
        
        if z_norm < 1e-6:
            return None # The 3 atoms are in a straight line, invalid basis
            
        z_axis = z_axis / z_norm
        
        # Y-axis: perpendicular to X and Z
        y_axis = np.cross(z_axis, x_axis)
        
        # The Transformation Matrix
        rotation_matrix = np.vstack([x_axis, y_axis, z_axis])
        return p1, rotation_matrix

    def insert_pocket(self, pocket_id: str, points: np.ndarray):
        """
        Hashes a pocket's 3D geometry into the table.
        """
        if len(points) < 3:
            return
            
        # 1. Define the Local Frame using the first 3 atoms
        p1, p2, p3 = points[0], points[1], points[2]
        basis = self._get_local_basis(p1, p2, p3)
        
        if basis is None:
            return 
            
        origin, rot_matrix = basis
        
        # 2. Hash all the remaining atoms in the pocket
        for i in range(3, len(points)):
            # Translate to origin, then multiply by rotation matrix
            local_pt = np.dot(rot_matrix, (points[i] - origin))
            
            # Quantize (Round to the nearest grid bin) to handle slight shape variations
            hash_key = tuple(np.round(local_pt / self.bin_size).astype(int))
            
            # Insert into our Spatial Hash Table
            self.table[hash_key].append(pocket_id)

    def query_pocket(self, points: np.ndarray) -> dict:
        """
        Searches the hash table for structurally matching pockets.
        Returns a dictionary of {pocket_id: match_score}.
        """
        if len(points) < 3:
            return {}
            
        p1, p2, p3 = points[0], points[1], points[2]
        basis = self._get_local_basis(p1, p2, p3)
        
        if basis is None:
            return {}
            
        origin, rot_matrix = basis
        votes = defaultdict(int)
        
        # Check our query atoms against the database
        for i in range(3, len(points)):
            local_pt = np.dot(rot_matrix, (points[i] - origin))
            hash_key = tuple(np.round(local_pt / self.bin_size).astype(int))
            
            # If this geometric feature exists in our DB, cast a vote!
            if hash_key in self.table:
                for matched_pocket in self.table[hash_key]:
                    votes[matched_pocket] += 1
                    
        return dict(votes)

# ==========================================
# QUICK TEST (Run this file directly to test)
# ==========================================
if __name__ == "__main__":
    # Initialize our Unit 5 Spatial Hash Table
    geo_hash = GeometricHashTable(bin_size=2.0)
    
    # Let's create a fake protein pocket (Target) with 5 atoms
    # Shape: [X, Y, Z]
    db_pocket = np.array([
        [0.0, 0.0, 0.0],  # Atom 1
        [5.0, 0.0, 0.0],  # Atom 2
        [0.0, 5.0, 0.0],  # Atom 3
        [2.0, 2.0, 5.0],  # Atom 4 (The unique feature)
        [1.0, 1.0, 1.0]   # Atom 5
    ])
    
    # 1. Insert into database
    print("Indexing Database Pocket: Target_COVID_Spike...")
    geo_hash.insert_pocket("Target_COVID_Spike", db_pocket)
    
    # 2. Create a Query Pocket. 
    # We will take the exact same pocket, but add 10 to every coordinate (Translating) 
    # and shuffle the coordinates around to simulate a rotated scan.
    query_pocket = db_pocket + np.array([10.0, -15.0, 42.0]) 
    
    print("Querying system with shifted coordinates...")
    results = geo_hash.query_pocket(query_pocket)
    
    print("\n--- Search Results ---")
    if results:
        for pocket, score in results.items():
            print(f"Match Found! Protein: {pocket} | Confidence Score: {score}/2")
    else:
        print("No matches found.")