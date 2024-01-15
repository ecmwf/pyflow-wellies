# Welcome to wellies documentation

Wellies provides extra features to help you build consistent and configurable 
pyflow suites. This guide assumes a good level of familiarity with 
[ecflow](https://ecflow.readthedocs.io) suites and using 
[pyflow](http://pyflow-workflow-generator.readthedocs.io) for its design and 
generation. Please refer to these projects' documentantion if some point about 
them is not clear.

## Main features

- ***YAML*-based configuration** for your suites: wellies provides simple 
patterns 
to help configuring your suite, making them more flexible and suitable for 
different use cases and environments.
- Simple template to start your **suite design from scratch**: Don't get blocked
by a blanck page; with `wellies-quickstart` starting to code a new workflow is 
one command away.
- **Git-tracked suite deployment** from [tracksuite](https://github.com/ecmwf/tracksuite): Wellies comes fully integrated with tracksuite providing git-based 
changes control for multi-users and remote deployment environments.
- **Extended *pyflow* nodes** for improved suite design, configuration and monitoring.
- **Template scripts** for improved reproducibility and support to D-R-Y design when it comes to scripting, like when dealing with datetime objects, *MARS* requests and others.

## Installation

Wellies is a pure python package, so installation from source is straightforward
with `pip`

```shell
git clone ssh://git@git.ecmwf.int/ecflow/wellies.git
cd wellies
pip install .
```

## Quickstart

The quickest way to get familiar with wellies' features is using the 
`wellies-quickstart` command-line tool to start a project from zero.

```python exec="true" id="quickstart-help"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.quickstart import get_parser
help_message=get_parser().format_help()
help_message = help_message.replace("mkdocs", "wellies-quickstart")
print(f"```\n{help_message}\n```")
```

To start a new project in a `projects` directory, just run

```shell
$ wellies-quickstart -p mysuite projects
```

This will create the following structure in your target project directory:

```tree
projects
    configs/
        config.yaml
        data.yaml
        execution_contexts.yaml
        tools.yaml
    suite/
        nodes.py
    deploy.py
    Makefile
```

Although it does not contain any meaningful task, this is already a **valid 
defined ecFlow suite**. To deploy all of the suite's scripts and write its definition file, just run:

```bash
$ ./deploy.py -y configs/*.yaml
```

and after loading it on a running ecflow server it will give the suite

![Template suite](img/mysuite.png)

*Template suite on ecflow*

This will provide a starting base for your suite. From there you can modify the 
project towards your own workflow.

The [Tutorials](quickstart_guide.md) section contains further examples on suite 
development from this base structure.

For details about how wellies can help configuring your suites, please check one 
of the [Suite Configuration](configurations.md) section.