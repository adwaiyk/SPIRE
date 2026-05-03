#pragma once
#include <vector>
#include <string>
#include <functional>

class BloomFilter {
private:
    int size;
    int num_hashes;
    std::vector<bool> bit_array;

public:
    BloomFilter(int size, int num_hashes) : size(size), num_hashes(num_hashes) {
        bit_array.resize(size, false);
    }

    BloomFilter(int size, int num_hashes, const std::vector<bool>& state) 
        : size(size), num_hashes(num_hashes), bit_array(state) {}

    void add(const std::string& item) {
        std::hash<std::string> hasher;
        for (int i = 0; i < num_hashes; ++i) {
            size_t hash_val = hasher(item + std::to_string(i)) % size;
            bit_array[hash_val] = true;
        }
    }

    bool check(const std::string& item) {
        std::hash<std::string> hasher;
        for (int i = 0; i < num_hashes; ++i) {
            size_t hash_val = hasher(item + std::to_string(i)) % size;
            if (!bit_array[hash_val]) return false;
        }
        return true;
    }

    int get_size() const { return size; }
    int get_num_hashes() const { return num_hashes; }
    std::vector<bool> get_bit_array() const { return bit_array; }
};