#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <string>
#include <functional>

namespace py = pybind11;

class BloomFilter
{
private:
    int size;
    int num_hashes;
    std::vector<bool> bit_array;

public:
    // Standard constructor
    BloomFilter(int size, int num_hashes) : size(size), num_hashes(num_hashes)
    {
        bit_array.resize(size, false);
    }

    // NEW: Internal constructor specifically for unpickling (loading from disk)
    BloomFilter(int size, int num_hashes, const std::vector<bool> &state)
        : size(size), num_hashes(num_hashes), bit_array(state) {}

    // Add item to the filter
    void add(const std::string &item)
    {
        std::hash<std::string> hasher;
        for (int i = 0; i < num_hashes; ++i)
        {
            size_t hash_val = hasher(item + std::to_string(i)) % size;
            bit_array[hash_val] = true;
        }
    }

    // Check if item exists (O(1) lookup)
    bool check(const std::string &item)
    {
        std::hash<std::string> hasher;
        for (int i = 0; i < num_hashes; ++i)
        {
            size_t hash_val = hasher(item + std::to_string(i)) % size;
            if (!bit_array[hash_val])
                return false;
        }
        return true;
    }

    // NEW: Getters so the pickler can read the private C++ memory
    int get_size() const { return size; }
    int get_num_hashes() const { return num_hashes; }
    std::vector<bool> get_bit_array() const { return bit_array; }
};

// --- PYBIND11 WRAPPER ---
PYBIND11_MODULE(spire_core, m)
{
    m.doc() = "SPIRE High-Performance C++ Core Plugin";

    py::class_<BloomFilter>(m, "BloomFilter")
        .def(py::init<int, int>(), py::arg("size"), py::arg("num_hashes"))
        .def("add", &BloomFilter::add, "Add an element to the Bloom Filter")
        .def("check", &BloomFilter::check, "Check if an element is in the Bloom Filter")

        // NEW: The serialization interface
        .def(py::pickle(
            [](const BloomFilter &p) { // __getstate__ (Saving)
                // Pack the C++ state into a Python tuple
                return py::make_tuple(p.get_size(), p.get_num_hashes(), p.get_bit_array());
            },
            [](py::tuple t) { // __setstate__ (Loading)
                if (t.size() != 3)
                    throw std::runtime_error("Invalid state!");

                // Unpack the Python tuple back into a C++ object
                return BloomFilter(
                    t[0].cast<int>(),
                    t[1].cast<int>(),
                    t[2].cast<std::vector<bool>>());
            }));
}