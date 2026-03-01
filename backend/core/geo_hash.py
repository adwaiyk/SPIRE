import numpy as np
from collections import defaultdict

class GeometricHashTable:
    """
    Unit 5 Data Structure: Maps 3D rotation-invariant shapes into O(1) hash buckets.
    Acts as a spatial gatekeeper before the VP-Tree traversal.
    """
    def __init__(self, bin_size=20.0):
        self.table = defaultdict(list)
        self.bin_size = bin_size

    def _quantize(self, vector: np.ndarray) -> tuple:
        """Converts continuous float coordinates into discrete integer buckets."""
        return tuple(np.round(np.array(vector) / self.bin_size).astype(int))

    def insert(self, protein_id: str, shape_vector: np.ndarray):
        """Hashes a protein into a rotation-invariant spatial bucket."""
        bucket_key = self._quantize(shape_vector)
        self.table[bucket_key].append(protein_id)

    def get_candidates(self, query_vector: np.ndarray) -> list:
        """Retrieves all protein candidates sharing the same relative spatial geometry."""
        bucket_key = self._quantize(query_vector)
        return self.table.get(bucket_key, [])