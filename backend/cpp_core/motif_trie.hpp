#pragma once
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <unordered_map>
#include <vector>
#include <string>
#include <algorithm>

namespace py = pybind11;

// The N-ary Tree Node
struct TrieNode {
    std::unordered_map<char, TrieNode*> children;
    std::vector<std::string> protein_ids; // Tracks which proteins contain this sequence

    ~TrieNode() {
        for (auto& pair : children) {
            delete pair.second;
        }
    }
};

class MotifTrie {
private:
    TrieNode* root;

    // Helper: Inserts a single suffix into the tree
    void insert_suffix(const std::string& suffix, const std::string& protein_id, int max_depth) {
        TrieNode* current = root;
        for (int i = 0; i < suffix.length() && i < max_depth; ++i) {
            char c = suffix[i];
            if (current->children.find(c) == current->children.end()) {
                current->children[c] = new TrieNode();
            }
            current = current->children[c];
            
            // Only add the protein ID if it's not already the last one in the list (prevents duplicates)
            if (current->protein_ids.empty() || current->protein_ids.back() != protein_id) {
                current->protein_ids.push_back(protein_id);
            }
        }
    }

public:
    MotifTrie() {
        root = new TrieNode();
    }
    
    ~MotifTrie() {
        delete root;
    }

    // $O(L^2)$ insertion per protein, but strictly capped at max_motif_length for memory safety
    void insert_sequence(const std::string& protein_id, const std::string& sequence) {
        int max_motif_length = 25; // Biological drug motifs are rarely longer than 25 Amino Acids
        for (size_t i = 0; i < sequence.length(); ++i) {
            insert_suffix(sequence.substr(i), protein_id, max_motif_length);
        }
    }

    // $O(m)$ Search Time: Lightning fast retrieval
    std::vector<std::string> search_motif(const std::string& motif) {
        TrieNode* current = root;
        for (char c : motif) {
            if (current->children.find(c) == current->children.end()) {
                return {}; // Path dead-ends; motif does not exist
            }
            current = current->children[c];
        }
        return current->protein_ids;
    }
};