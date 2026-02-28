import math
import mmh3
from bitarray import bitarray

class ChemicalBloomFilter:
    """
    Unit 6 Data Structure: Bloom Filter
    Used in SPIRE to quickly prune protein pockets that lack 
    the necessary physicochemical properties before spatial hashing.
    """
    def __init__(self, expected_items: int, false_positive_rate: float):
        """
        Initializes the bit array based on optimal mathematical constraints.
        """
        self.expected_items = expected_items
        self.fp_rate = false_positive_rate
        
        # Calculate optimal size (m) and hash functions (k)
        self.size = self.get_optimal_size(expected_items, false_positive_rate)
        self.hash_count = self.get_optimal_hash_count(self.size, expected_items)
        
        # Initialize the bit array with all zeros
        self.bit_array = bitarray(self.size)
        self.bit_array.setall(0)

    @classmethod
    def get_optimal_size(cls, n: int, p: float) -> int:
        """ Calculates optimal bit array size """
        m = -(n * math.log(p)) / (math.log(2) ** 2)
        return int(m)

    @classmethod
    def get_optimal_hash_count(cls, m: int, n: int) -> int:
        """ Calculates optimal number of hash functions """
        k = (m / n) * math.log(2)
        return int(k)

    def add(self, property_string: str):
        """
        Hashes the chemical property and sets the corresponding bits to 1.
        """
        for i in range(self.hash_count):
            # Use 'i' as the seed for mmh3 to simulate multiple hash functions
            digest = mmh3.hash(property_string, i) % self.size
            self.bit_array[digest] = 1

    def check(self, property_string: str) -> bool:
        """
        Checks if the chemical property might exist.
        Returns False if definitely not present.
        Returns True if probably present.
        """
        for i in range(self.hash_count):
            digest = mmh3.hash(property_string, i) % self.size
            if self.bit_array[digest] == 0:
                return False  # Definitely not present
        return True  # Probably present


# ==========================================
# QUICK TEST (Run this file directly to test)
# ==========================================
if __name__ == "__main__":
    # Initialize filter: expect 10 properties per pocket, 1% false positive rate
    pocket_filter = ChemicalBloomFilter(expected_items=10, false_positive_rate=0.01)
    
    # Let's say we process a pocket and extract its chemical properties
    actual_properties = ["HYDROPHOBIC", "HAS_SULPHUR", "CHARGE_POSITIVE"]
    for prop in actual_properties:
        pocket_filter.add(prop)
        
    print(f"Filter Size: {pocket_filter.size} bits")
    print(f"Hash Functions: {pocket_filter.hash_count}")
    
    # 1. Test for a property we know is there (Should be True)
    print("\nChecking 'HAS_SULPHUR':", pocket_filter.check("HAS_SULPHUR"))
    
    # 2. Test for a property we know is NOT there (Should be False)
    print("Checking 'CHARGE_NEGATIVE':", pocket_filter.check("CHARGE_NEGATIVE"))