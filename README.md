<h3 align="center">
<picture>
    <source srcset="https://raw.githubusercontent.com/ecmwf/logos/feature/add-logo-pyflow_wellies-20250501113719/logos/pyflow/logo_wellies_dark.svg" media="(prefers-color-scheme: dark)">
    <img src="https://raw.githubusercontent.com/ecmwf/logos/feature/add-logo-pyflow_wellies-20250501113719/logos/pyflow/logo_wellies_light.svg" width="100">
  </picture>
</br>
</h3>


<p align="center">
   <a href="https://github.com/ecmwf/codex/raw/refs/heads/main/ESEE">
    <img src="https://raw.githubusercontent.com/ecmwf/codex/refs/heads/main/ESEE/production_chain_badge.svg" alt="ESEE Production Chain">
  </a>
  <a href="https://github.com/ecmwf/codex/blob/refs/heads/main/Project%20Maturity/readme.md">
    <img src="https://img.shields.io/badge/Maturity-Incubating-lightskyblue" alt="Maturity Incubating">
  </a>
  <!-- <a href="https://codecov.io/gh/ecmwf/pyflow_wellies">
    <img src="https://codecov.io/gh/ecmwf/pyflow_wellies/branch/develop/graph/badge.svg" alt="Code Coverage">
  </a> -->
  <a href="https://opensource.org/licenses/apache-2-0">
    <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License: Apache 2.0">
  </a>
  <a href="https://github.com/ecmwf/pyflow-wellies/releases">
    <img src="https://img.shields.io/github/v/release/ecmwf/pyflow-wellies?color=purple&label=Release" alt="Latest Release">
  </a>
  <a href="https://pyflow-wellies.readthedocs.io/latest">
    <img src="https://readthedocs.org/projects/pyflow-wellies/badge/?version=latest" alt="Documentation Status">
  </a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#installation">Installation</a> •
  <a href="#contributing">Contributing</a> •
<!--   <a href="#contributors">Contributors</a> • -->
  <a href="https://pyflow-wellies.readthedocs.io/latest/">Documentation</a>
</p>


# pyflow-wellies

> \[!IMPORTANT\]
> This software is **Incubating** and subject to ECMWF's guidelines on [Software Maturity](https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity).

Wellies provides extra features to help you build consistent and configurable
pyflow suites. This guide assumes a good level of familiarity with
[ecflow](https://ecflow.readthedocs.io) suites and using
[pyflow](http://pyflow-workflow-generator.readthedocs.io) for its design and
generation. Please refer to these projects' documentantion if some point about
them is not clear.

# Features

- ***YAML*-based configuration** for your suites: wellies provides simple
patterns to help configuring your suite, making them more flexible and suitable for
different use cases and environments.
- Simple template to start your **suite design from scratch**: Don't get blocked
by a blanck page; with `wellies-quickstart` starting to code a new workflow is
one command away.
- **Git-tracked suite deployment** from [tracksuite](https://github.com/ecmwf/tracksuite): Wellies comes fully integrated with tracksuite providing git-based changes control for multi-users and remote deployment environments.
- **Extended *pyflow* nodes** for improved suite design, configuration and monitoring.
- **Template scripts** for improved reproducibility and support to D-R-Y design when it comes to scripting, like when dealing with datetime objects, *MARS* requests and others.

# Quick Start

To create an empty suite with the default wellies structure, simply run

```
wellies-quickstart /path/to/project -p mysuite
```

Once created the suite can be build with:

```
cd /path/to/project
./mysuite.py configs/*.yaml
```

which is equivalent to

```
./mysuite.py configs/config.yaml config/tools.yaml configs/data.yaml config/execution_contexts.yaml
```

You can also cherry pick your configuration files following your needs:

```
cd /path/to/project
./mysuite.py configs/config.yaml config/tools.yaml
```

Alternatively you use named preset groups of configurations defined in a default `Makefile` and just use

```
make
```

# Installation

First you need to assure you have [ecFlow](https://ecflow.readthedocs.io/en/latest/) installed on your system.
The simplest way is to create a conda environment. We recommend using
[mamba](https://mamba.readthedocs.io/en/latest/index.html) to speed up the environment creation process:

```
mamba create -c conda-forge -n wellies-env python=3.10 ecflow
conda activate wellies-env
```

Install from the Github repository directly:
```
python -m pip install https://github.com/ecmwf/pyflow-wellies
```
or from PyPI:
```
python -m pip install pyflow-wellies
```

## License

See [LICENSE](LICENSE)

```
In applying this licence, ECMWF does not waive the privileges and immunities
granted to it by virtue of its status as an intergovernmental organisation
nor does it submit to any jurisdiction.
```

## Copyright

© 2023 ECMWF. All rights reserved.

# Contributing

First build a development conda environment

```
mamba env create -f ./environment.yml -n wellies-env
conda activate wellies-env
```

Then install with development dependencies

```
git clone https://github.com/ecmwf/pyflow-wellies.git
cd pyflow-wellies
pip install -e .[dev]
```

## Building package

To build source distributions, [build](https://build.pypa.io/en/stable/index.html) is required.
With that the source distribution can be built from any environment with

```
git clone https://github.com/ecmwf/pyflow-wellies.git
cd pyflow-wellies
python -m build
```

## Testing

To run tests, first install testing dependencies:

```
git clone https://github.com/ecmwf/pyflow-wellies.git
cd pyflow-wellies
pip install .[test]
```

Then to run all tests
```
python -m pytest
```

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
