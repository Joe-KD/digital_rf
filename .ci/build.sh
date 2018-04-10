#!/bin/bash
set -e -x

echo $PATH
which python

# build libraries
mkdir build
cd build
cmake ..
make

# make python source distribution (for upload to PyPI)
make digital_rf_sdist

# install python package into virtual environment for testing
python -m pip install dist/digital_rf-*.tar.gz
