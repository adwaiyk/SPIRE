#pragma once
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <string>
#include <unordered_map>
#include <cmath>

namespace py = pybind11;

class GeometricHashTable {
private:
    double bin_size;
    std::unordered_map<std::string, std::vector<std::string>> table;

    std::string get_bin_key(py::array_t<double> vec) {
        auto r = vec.unchecked<1>(); // Direct memory access
        std::string key = "";
        for (py::ssize_t i = 0; i < r.shape(0); i++) {
            long bin = std::round(r(i) / bin_size);
            key += std::to_string(bin) + "_";
        }
        return key;
    }

public:
    GeometricHashTable(double bin_size) : bin_size(bin_size) {}

    GeometricHashTable(double bin_size, const std::unordered_map<std::string, std::vector<std::string>>& state)
        : bin_size(bin_size), table(state) {}

    void insert(const std::string& pid_pocket, py::array_t<double> vec) {
        std::string key = get_bin_key(vec);
        table[key].push_back(pid_pocket);
    }

    std::vector<std::string> get_candidates(py::array_t<double> vec) {
        std::string key = get_bin_key(vec);
        if (table.find(key) != table.end()) {
            return table[key];
        }
        return std::vector<std::string>(); 
    }

    double get_bin_size() const { return bin_size; }
    std::unordered_map<std::string, std::vector<std::string>> get_table() const { return table; }
};