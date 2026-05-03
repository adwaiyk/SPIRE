from setuptools import setup, Extension
import pybind11
import os

# Define the C++ extension module
ext_modules = [
    Extension(
        "spire_core", # The name of the compiled module
        ["cpp_core/spire_core.cpp"], # The source file we wrote
        include_dirs=[pybind11.get_include()], # Automatically finds the correct headers!
        language='c++',
        extra_compile_args=['-O3', '-Wall', '-std=c++11', '-fPIC'],
    ),
]

setup(
    name="spire_core",
    ext_modules=ext_modules,
)