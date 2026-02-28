import numpy as np

class VPNode:
    """ A node in the Vantage Point Tree. """
    def __init__(self, vantage_point, radius, pocket_id, left=None, right=None):
        self.vp = vantage_point      # The feature vector of this pocket
        self.radius = radius         # The median distance to other points
        self.pocket_id = pocket_id   # The name/ID of the protein
        self.left = left             # Inside the radius
        self.right = right           # Outside the radius

class VPTree:
    """
    Unit 5 Data Structure: Vantage Point Tree
    Used for efficient Nearest Neighbor Search in high-dimensional metric spaces.
    """
    def __init__(self, points, ids):
        # We zip the 3D feature vectors with their string IDs so we don't lose the names
        data = list(zip(points, ids))
        self.root = self._build_tree(data)

    def _euclidean_distance(self, p1, p2):
        """ The Metric Space distance function. """
        return np.linalg.norm(p1 - p2)

    def _build_tree(self, data):
        """ Recursively builds the tree by finding medians. """
        if not data:
            return None

        # 1. Pick the first item as the Vantage Point (VP)
        vp, pocket_id = data[0]
        
        if len(data) == 1:
            return VPNode(vp, 0, pocket_id)

        # 2. Calculate distances from the VP to all other points
        rest = data[1:]
        distances = [self._euclidean_distance(vp, point) for point, _ in rest]
        
        # 3. Find the median distance to draw our "Sphere"
        median_radius = np.median(distances)

        # 4. Partition the data: Inside the sphere (Left) vs Outside (Right)
        left_data = [item for i, item in enumerate(rest) if distances[i] <= median_radius]
        right_data = [item for i, item in enumerate(rest) if distances[i] > median_radius]

        # 5. Recursively build the children
        return VPNode(
            vantage_point=vp,
            radius=median_radius,
            pocket_id=pocket_id,
            left=self._build_tree(left_data),
            right=self._build_tree(right_data)
        )

    def search_nearest(self, query_point):
        """
        Searches the tree for the single closest pocket in O(log N) time.
        """
        self.best_distance = float('inf')
        self.best_match = None

        def _search(node):
            if node is None:
                return

            # Calculate distance from query to the current node's Vantage Point
            dist = self._euclidean_distance(query_point, node.vp)

            # Is this the closest we've seen so far?
            if dist < self.best_distance:
                self.best_distance = dist
                self.best_match = node.pocket_id

            # Decide which child to search first based on whether the query
            # falls inside or outside this node's radius
            if dist < node.radius:
                first_child = node.left
                second_child = node.right
            else:
                first_child = node.right
                second_child = node.left

            # Always search the most likely child
            _search(first_child)

            # CRITICAL PRUNING STEP:
            # Only search the other side if the "sphere" of our current best match
            # overlaps with the boundary of this node's radius.
            if abs(dist - node.radius) < self.best_distance:
                _search(second_child)

        _search(self.root)
        return self.best_match, self.best_distance

# ==========================================
# QUICK TEST (Run this file directly to test)
# ==========================================
if __name__ == "__main__":
    print("Building VP-Tree with Database Pockets...")
    
    # Fake database of protein pockets turned into feature vectors
    db_points = np.array([
        [1.0, 2.0, 3.0],   # Liver_Protein_A
        [10.0, 10.0, 10.0],# Heart_Protein_B
        [5.0, 5.0, 5.0],   # Brain_Protein_C
        [100.0, 0.0, 0.0]  # Random_Junk_Protein
    ])
    db_ids = ["Liver_Protein_A", "Heart_Protein_B", "Brain_Protein_C", "Random_Junk_Protein"]

    # Build the tree (This happens once during server startup)
    tree = VPTree(db_points, db_ids)

    # A query comes in from the Frontend! 
    # It's very close to [10, 10, 10], so it should match the Heart Protein.
    query = np.array([9.5, 10.2, 9.8])
    
    print(f"\nSearching for nearest match to query vector: {query}")
    best_pocket, distance = tree.search_nearest(query)
    
    print(f"Top Match: {best_pocket}")
    print(f"Distance Score: {distance:.4f} (Lower is better)")