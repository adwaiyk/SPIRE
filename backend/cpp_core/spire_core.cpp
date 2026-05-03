#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "bloom_filter.hpp"
#include "geo_hash.hpp"
#include "vp_tree.hpp"
#include "motif_trie.hpp"

namespace py = pybind11;

PYBIND11_MODULE(spire_core, m) {
    m.doc() = "SPIRE High-Performance C++ Core Plugin";

    // Bind Bloom Filter
    py::class_<BloomFilter>(m, "BloomFilter")
        .def(py::init<int, int>(), py::arg("size"), py::arg("num_hashes"))
        .def("add", &BloomFilter::add)
        .def("check", &BloomFilter::check)
        .def(py::pickle(
            [](const BloomFilter &p) { return py::make_tuple(p.get_size(), p.get_num_hashes(), p.get_bit_array()); },
            [](py::tuple t) { return BloomFilter(t[0].cast<int>(), t[1].cast<int>(), t[2].cast<std::vector<bool>>()); }
        ));

    // Bind Geometric Hash Table
    py::class_<GeometricHashTable>(m, "GeometricHashTable")
        .def(py::init<double>(), py::arg("bin_size") = 20.0)
        .def("insert", &GeometricHashTable::insert)
        .def("get_candidates", &GeometricHashTable::get_candidates)
        .def(py::pickle(
            [](const GeometricHashTable &p) { return py::make_tuple(p.get_bin_size(), p.get_table()); },
            [](py::tuple t) { return GeometricHashTable(t[0].cast<double>(), t[1].cast<std::unordered_map<std::string, std::vector<std::string>>>()); }
        ));

    // Bind VP-Tree
    py::class_<VPTree>(m, "VPTree")
        .def(py::init<>())
        .def("add", &VPTree::add, "Add an item to the tree structure")
        .def("build", &VPTree::build, "Compile the tree after adding all items")
        .def("search_nearest", &VPTree::search_nearest, py::arg("vec"), py::arg("k") = 1, "O(log N) nearest neighbor search")
        .def(py::pickle(
            [](const VPTree &p) { // Save: Pack the raw data
                return py::make_tuple(p.get_state());
            },
            [](py::tuple t) { // Load: Unpack and auto-rebuild the tree pointers
                return VPTree(t[0].cast<std::vector<std::pair<std::string, std::vector<double>>>>());
            }
        ));

        py::class_<MotifTrie>(m, "MotifTrie")
        .def(py::init<>())
        .def("insert_sequence", &MotifTrie::insert_sequence, "Index a 1D protein sequence")
        .def("search_motif", &MotifTrie::search_motif, "O(m) motif search");
}