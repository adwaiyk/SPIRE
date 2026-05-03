#pragma once
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <limits>
#include <tuple>

namespace py = pybind11;

// A simple structure to hold our spatial data
struct DataPoint {
    std::string id;
    std::vector<double> coords;
};

// The recursive Node structure
struct Node {
    DataPoint vp;          // The Vantage Point
    double threshold;      // The median distance radius
    Node* inside;          // Points inside the radius
    Node* outside;         // Points outside the radius

    Node() : threshold(0.0), inside(nullptr), outside(nullptr) {}
    ~Node() {
        delete inside;
        delete outside;
    }
};

class VPTree {
private:
    Node* root;
    std::vector<DataPoint> all_items; // Flat storage for easy pickling

    // High-speed Euclidean distance calculation
    double distance(const std::vector<double>& a, const std::vector<double>& b) const {
        double sum = 0.0;
        for (size_t i = 0; i < a.size(); ++i) {
            double diff = a[i] - b[i];
            sum += diff * diff;
        }
        return std::sqrt(sum);
    }

    // Recursive tree builder
    Node* buildFromPoints(int lower, int upper) {
        if (lower == upper) return nullptr;

        Node* node = new Node();
        node->vp = all_items[lower];

        if (lower + 1 == upper) {
            return node;
        }

        // Calculate distances from the vantage point to all other points
        int median_idx = lower + 1 + (upper - lower - 1) / 2;
        std::nth_element(
            all_items.begin() + lower + 1,
            all_items.begin() + median_idx,
            all_items.begin() + upper,
            [this, &node](const DataPoint& a, const DataPoint& b) {
                return distance(node->vp.coords, a.coords) < distance(node->vp.coords, b.coords);
            }
        );

        node->threshold = distance(node->vp.coords, all_items[median_idx].coords);
        node->inside = buildFromPoints(lower + 1, median_idx);
        node->outside = buildFromPoints(median_idx, upper);

        return node;
    }

    // Recursive nearest-neighbor search
    void search(Node* node, const std::vector<double>& target, int k, double& tau, std::vector<std::pair<double, std::string>>& results) {
        if (!node) return;

        double dist = distance(node->vp.coords, target);

        if (dist < tau) {
            results.push_back({dist, node->vp.id});
            std::sort(results.begin(), results.end());
            if (results.size() > (size_t)k) {
                results.pop_back();
            }
            if (results.size() == (size_t)k) {
                tau = results.back().first;
            }
        }

        if (!node->inside && !node->outside) return;

        if (dist < node->threshold) {
            if (dist - tau <= node->threshold) search(node->inside, target, k, tau, results);
            if (dist + tau >= node->threshold) search(node->outside, target, k, tau, results);
        } else {
            if (dist + tau >= node->threshold) search(node->outside, target, k, tau, results);
            if (dist - tau <= node->threshold) search(node->inside, target, k, tau, results);
        }
    }

public:
    VPTree() : root(nullptr) {}
    ~VPTree() { delete root; }

    // Internal constructor for unpickling
    VPTree(const std::vector<std::pair<std::string, std::vector<double>>>& state) : root(nullptr) {
        for (const auto& item : state) {
            all_items.push_back({item.first, item.second});
        }
        build();
    }

    // Add items iteratively
    void add(const std::string& id, py::array_t<double> vec) {
        auto r = vec.unchecked<1>();
        std::vector<double> v(r.data(0), r.data(0) + r.shape(0));
        all_items.push_back({id, v});
    }

    // Lock and build the tree (O(N log N))
    void build() {
        delete root; // Clear old tree if rebuilding
        root = buildFromPoints(0, all_items.size());
    }

    // Retrieve nearest neighbors (O(log N))
    py::list search_nearest(py::array_t<double> vec, int k = 1) {
        auto r = vec.unchecked<1>();
        std::vector<double> target(r.data(0), r.data(0) + r.shape(0));

        std::vector<std::pair<double, std::string>> results;
        double tau = std::numeric_limits<double>::max();

        search(root, target, k, tau, results);

        // Convert C++ results back to Python list
        py::list py_results;
        for (const auto& res : results) {
            py_results.append(py::make_tuple(res.second, res.first)); // (ID, Distance)
        }
        return py_results;
    }

    // Expose flat data for pickling
    std::vector<std::pair<std::string, std::vector<double>>> get_state() const {
        std::vector<std::pair<std::string, std::vector<double>>> state;
        for (const auto& item : all_items) {
            state.push_back({item.id, item.coords});
        }
        return state;
    }
};