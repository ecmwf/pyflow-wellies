![](logo_wellies.png)

# Wellies

A set of tools to build consistent pyflow suites.

# with pip

First you need to assure you have [ecFlow](https://ecflow.readthedocs.io/en/latest/) installed on your system. 
The simplest way is to create a conda environment. We recommend using 
[mamba](https://mamba.readthedocs.io/en/latest/index.html) to speed up the environment creation process:

    $ mamba create -c conda-forge -n wellies-env python=3.10 ecflow
    $ conda activate wellies-env

Then, wellies can be installed directly with pip

    $ python -m pip pyflow-wellies

## from source

First, build a conda environment with all the dependencies

    mamba env create -f ./environment.yml -n wellies-env
    conda activate wellies-env

Then, install wellies in your environment:

    pip install .

# Quickstart

## Create empty suite

To create an empty suite with the default wellies structure, simply run

    wellies-quickstart /path/to/project -p mysuite

Once created the suite can be build this:

    cd /path/to/project
    ./mysuite.py configs/*.yaml

which is equivalent to

    ./mysuite.py configs/config.yaml config/tools.yaml configs/data.yaml config/execution_contexts.yaml

You can also cherry pick your configuration files following your needs:

    cd /path/to/project
    ./mysuite.py configs/config.yaml config/tools.yaml


# Contributing

## Building package

To build source distributions, [build](https://build.pypa.io/en/stable/index.html) is required. 
With that the source distribution can be built from any environment with

    git clone https://github.com/ecmwf/pyflow-wellies.git
    cd pyflow-wellies
    python -m build

## Testing

To run tests, first install testing dependencies:

    git clone https://github.com/ecmwf/pyflow-wellies.git
    cd pyflow-wellies
    pip install .[test]

Then to run all tests

    python -m pytest

To run individual tests:

    python -m pytest tests/test_data.py::test_rsync_data

## Documentation

To build your own local documentation you need [mkdocs](https://www.mkdocs.org) and a few 
entra plugins. As there are many auto-generated parts in the documentation, 
you will need a environment with wellies and all of its dependencies installed to build the documentation. 
To install the documentation-only dependencies:

    git clone https://github.com/ecmwf/pyflow-wellies.git
    cd pyflow-wellies
    pip install .[docs]

Then to build it

    mkdocs build

To build and make it available in a local server

    mkdocs serve
