class TrieNode:
    def __init__(self):
        self.children = {}
        self.protein_ids = []

class MotifTrie:
    def __init__(self):
        self.root = TrieNode()

    def _insert_suffix(self, suffix: str, protein_id: str, max_depth: int):
        current = self.root
        for i in range(min(len(suffix), max_depth)):
            char = suffix[i]
            if char not in current.children:
                current.children[char] = TrieNode()
            current = current.children[char]
            
            # Only add the protein ID if it's not already the last one (prevents duplicates)
            if not current.protein_ids or current.protein_ids[-1] != protein_id:
                current.protein_ids.append(protein_id)

    def insert_sequence(self, protein_id: str, sequence: str):
        """
        Indexes every possible substring of the protein up to a length of 25.
        Biological drug motifs are rarely longer than 25 Amino Acids.
        """
        max_motif_length = 25 
        for i in range(len(sequence)):
            self._insert_suffix(sequence[i:], protein_id, max_motif_length)

    def search_motif(self, motif: str) -> list:
        """
        O(m) Search Time: Lightning fast retrieval where 'm' is motif length.
        """
        current = self.root
        for char in motif:
            if char not in current.children:
                return [] # Path dead-ends; motif does not exist
            current = current.children[char]
        return current.protein_ids