![](logo_wellies.png)

# Wellies

A set of tools to build consistent pyflow suites.

## Installation

Install Wellies in your environment:

    pip install .

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


## Testing

To run all tests:

    python -m pytest

To run individual tests:

    python -m pytest tests/test_data.py::test_rsync_data