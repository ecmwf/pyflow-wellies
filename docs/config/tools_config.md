# Tools

Wellies defines a `Tool` as anything that needs to be made available on the
execution environment of one or more of your workflow's tasks. They can be
dependent on each other and contain up to three script snippets that will be
used on different contexts:

- `#!python setup`: Defines how a tool can be installed on the suite's workspace.
- `#!python load`: For any occasion when preparation action needs to be done to make a
tool discoverable for use.
- `#!python unload`: The opposite operation of load. Makes the tool not available
anymore.

## Tool types

- **Environment variable**: general environment variables with `name` and `value`
that can be set at configuration level.
- **Module**: They are just loaded/unloaded from the system, i.e., does not have
a setup. At configuration level the options are `name` and `version`. Can be a
general [Module][wellies.tools.ModuleTool] or
[Private][wellies.tools.PrivateModuleTool] which requires an extra option
`modulefiles`.
- **Package**: They are installables that can be retrieved from local or remote
locations. The options are similar to the ones for the different
[static data types](data_config.md) and the `post_script` option can be used to
reference to custom installation script snippets or commands. They don't add
`load` or `unload` scripts, so usually they are associated to an environment
where they can be made discoverable. A custom `build_dir` can be provided and that will
point the retrieval part of the setup script to that location.
- Python **virtual environment**: This is a shortcut to define python virtual
    environments that will be built using `venv`. Wellies supports two types
    - `type: system_venv`: Creates an environment that is based on the
    system-wide python installation, meaning the creation option will contain the
    `--system-site-packages` argument. Extra external packages can be installed
    locally to the environment using the `extra_packages` option.
    - `type: venv`: Creates a file-based environment without the
    `--system-site-packages` argument.
- **Conda environment**: Wellies supports three types of conda environments using
different building strategies: from a specification file when `env_file` is
present, with a list of packages provided when `extra_packages` is present, or
no build at all with a reference to an existing environment when `environment`
is present. Extra options for the conda commands can be set using the `conda_cmd`
option. The `env_file` behaves just as any other data object, so any of the
[static data types](data_config.md) can be use to define how the specification
file needs to be retrieved.
- **Folder environment**: This is namespace environment type where packages can be
installed with appropriate dependencies. The created namespace will be added to
the system `PATH` for discoverability.
- **Custom environment**: Custom environment with custom `load`, `unload` and `setup`
commands or scripts.

All Tool types also accept a `depends` option where a list of
dependencies can be defined by each tool `name`. Environment types accept a
`packages` option where previously defined package Tools can be installed on that
same environment

/// admonition | Warning
    type: warning
Please be aware that configuration files are parsed sequentially, so
the dependency tree must be defined accordingly.
///

## Examples

### Environment variables

```yaml title="tools.yaml"
tools:
  env_variables:
    PYTHONPATH:
      value: "$LIB_DIR/python:$LIB_DIR/bin"
    HDF5:
      variable: HDF5_USE_FILE_LOCKING
      value: "FALSE"
```

The wellies' generated snippets environment variables will be

```python exec="true" id="env_vars" result="shell"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.tools import parse_env_var
tool = parse_env_var(name="PYTHONPATH", options=dict(value="$LIB_DIR/python:$LIB_DIR/bin"))
for tt in ['setup', 'load', 'unload']:
    print(f"--------{tt} script-----------")
    sc = tool.scripts[tt]
    if sc:
        print('\n'.join(sc.generate_stub()))
    print()
```

If `variable` is provided, the high-level key will be an alias that you can refer
to in the python suite generator code of your suite that will point to the
actual variable name on the system. The snippets will reflect that.

```python exec="true" id="env_vars" result="shell"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.tools import parse_env_var
tool = parse_env_var(
    name="HDF5",
    options=dict(variable="HDF5_USE_FILE_LOCKING", value="FALSE")
)
for tt in ['setup', 'load', 'unload']:
    print(f"--------{tt} script-----------")
    sc = tool.scripts[tt]
    if sc:
        print('\n'.join(sc.generate_stub()))
    print()
```

/// admonition | Note
    type: hint
any environment variable ending with `"PATH"` will have a special treatment and
write the value in append mode.
///

### Modules

```yaml title="tools.yaml"
tools:
  modules:
    ecmwf-toolbox:
      version: "2023.10.1.0"
    mymodule:
      modulefiles: /path/to/dev/module
```

The wellies' generated snippets for the system module will be

```python exec="true" id="module_tool" result="shell"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.tools import parse_module
tool = parse_module(name="ecmwf-toolbox", options=dict(version="2023.10.1.0"))
for tt in ['setup', 'load', 'unload']:
    print(f"--------{tt} script-----------")
    sc = tool.scripts[tt]
    if sc:
        print('\n'.join(sc.generate_stub()))
    print()
```

And for private modules

```python exec="true" id="priv_module" result="shell"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.tools import parse_module
tool = parse_module(name="mymodule", options=dict(modulefiles="/path/to/dev/module"))
for tt in ['setup', 'load', 'unload']:
    print(f"--------{tt} script-----------")
    sc = tool.scripts[tt]
    if sc:
        print('\n'.join(sc.generate_stub()))
    print()
```

You can also differentiate between the configuration key and the actual module
name by providing a value for `name`. This makes it easier for cross-referencing
on dependencies trees while using various versions.

```yaml title="tools.yaml"
tools:
  modules:
    python:
      name: python3
      version: "3.10.10-01"
    python_old:
      name: python3
      version: "old"
    pyflow:
      version: "3.2.0"
      depends: ["python"]
    pcraster:
      version: "4.3.0-01"
      depends: ["python_old"]
```

After combined into a [wellies.ToolStore][] object, the dependencies can be
resolved accordingly. Using the configuration above, the `pyflow` tool will
contain the following snippets:

```python exec="true" id="deps_modules" result="shell"
import os,sys
import pyflow as pf
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.tools import ToolStore
toolstore = ToolStore(
    lib_dir="$LIB_DIR",
    options=dict(modules=dict(
        python=dict(name='python3', version='3.10.10-01'),
        pyflow=dict(version="3.2.0", depends=["python"]),
    )))
for tt in ['setup', 'load', 'unload']:
    print(f"--------{tt} script-----------")
    sc = toolstore.tool_script(tt, 'pyflow')
    if sc:
        print('\n'.join(pf.Script.generate_list_scripts(list(sc.values()))))
    print()
```


### Packages

```yaml title="tools.yaml"
tools:
  packages:
    earthkit:
      type: "git"
        source: "git@github.com:ecmwf/earthkit-data.git"
        branch: "develop"
        build_dir: "/tmp/git/files"
        post_script: [
          "pip uninstall earthkit",
          "pip install .",
          "pip show src | grep Version > version.txt",
        ]
    local_files:
      type: "rsync"
      source: "hpc-login:/path/to/pkg/src"
      post_script: "/path/to/installer.sh"
```

Considering there is a `LIB_DIR` environment variable pointing to where packages should be installed, the wellies' generated snippets for `earthkit` will be

```python exec="true" id="package_tool" result="shell"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
import pyflow as pf
from wellies.tools import parse_package
tool = parse_package(
    lib_dir="$LIB_DIR",
    name="earthkit",
    options=dict(
        type="git",
        source="git@github.com:ecmwf/earthkit-data.git",
        branch="develop",
        build_dir="/tmp/git/files",
        post_script=["pip uninstall earthkit", "pip install .", "pip show src | grep Version > version.txt"]
    )
)
for tt in ['setup', 'load', 'unload']:
    print(f"--------{tt} script-----------")
    sc = tool.scripts[tt]
    lines = []
    if isinstance(sc, pf.Script):
        lines=sc.generate_stub()
    elif isinstance(sc, list):
        lines=pf.Script.generate_list_scripts(sc)

    print('\n'.join(lines))
    print()
```

The package signature is based on the [StaticData][wellies.data.StaticData]
object. For supported types for different retrieval strategies, please check
[this page](data_config.md). Further customization in the setup process is
provided by the `post_script` option that can accept either a literal script or
a reference to an existing file.

So, using the example above once again, `local_files` will have the following
generated snippets:

```bash title='installer.sh'
echo "Hello from install file"
cd $LIB_DIR/local_files && make install
```


```python exec="true" id="package_rsync" result="shell"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
import pyflow as pf
from wellies.tools import parse_package
import tempfile

tmpfile = tempfile.NamedTemporaryFile('w', delete=False)
with tmpfile.file as fin:
    fin.write('echo "Hello from install file"\n')
    fin.write('cd $LIB_DIR/local_files && make install\n')

tool = parse_package(
    lib_dir="$LIB_DIR",
    name="local_files",
    options=dict(
        type="rsync",
        source="hpc-login:/path/to/pkg/src",
        post_script=tmpfile.name,
    )
)
for tt in ['setup', 'load', 'unload']:
    print(f"--------{tt} script-----------")
    sc = tool.scripts[tt]
    lines = []
    if isinstance(sc, pf.Script):
        lines=sc.generate_stub()
    elif isinstance(sc, list):
        lines=pf.Script.generate_list_scripts(sc)

    print('\n'.join(lines))
    print()
```

### Folder environment

Folder environments are like a namespace to aggregate different tools together.
Firstly, checking the environment itself:

```yaml title="tools.yaml"
tools:
  environments:
    bin:
      type: folder
```

Considering there is `LIB_DIR` environment variable pointing to the root
directory, the wellies' generated snippets will be

```python exec="true" id="folder_env" result="shell"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
import pyflow as pf
from wellies.tools import parse_environment
tool = parse_environment(
    lib_dir="$LIB_DIR",
    name="bin",
    options=dict(
        type="folder",
        depends=["python3"]
    )
)
for tt in ['setup', 'load', 'unload']:
    print(f"--------{tt} script-----------")
    sc = tool.scripts[tt]
    lines = []
    if isinstance(sc, pf.Script):
        lines=sc.generate_stub()
    elif isinstance(sc, list):
        lines=pf.Script.generate_list_scripts(sc)

    print('\n'.join(lines))
    print()
```

### Python virtual environment

#### System environment

The following config can be used to define a local python virtual environment
that extends a system wide installation:

```yaml title="tools.yaml"
tools:
  environments:
    myvenv:
      type: system_venv
      extra_packages: "pcraster>=3.4"
      venv_options: "--upgrade"
```

Considering there is `LIB_DIR` environment variable pointing to the
installation root directory, the wellies' generated snippets will be

```python exec="true" id="systemvenv_env" result="shell"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
import pyflow as pf
from wellies.tools import parse_environment
tool = parse_environment(
    lib_dir="$LIB_DIR",
    name="myvenv",
    options=dict(
        type="system_venv",
        extra_packages=["pcraster>=3.4"],
        venv_options=["--upgrade"]
    )
)
for tt in ['setup', 'load', 'unload']:
    print(f"--------{tt} script-----------")
    sc = tool.scripts[tt]
    lines = [sc]
    if isinstance(sc, pf.Script):
        lines=sc.generate_stub()
    elif isinstance(sc, list):
        lines=pf.Script.generate_list_scripts(sc)

    print('\n'.join(lines))
    print()
```

/// admonition | Note
    type: Note
the reserved name `packages` always refers to other tools of this type specified
within your configuration. For external packages use `extra_packages`
///

/// admonition | Warning
    type: warning
If provided, `extra_packages` must always be a list, even of one element
///

#### Build with custom packages

The following config can be used to define a local python virtual environment
that does not use the system-wide site-packages.

```yaml title="tools.yaml"
tools:
  environments:
    datasets_env:
      type: venv
      packages: [anemoi_datasets]
      depends: [python]
```

Considering there is `LIB_DIR` environment variable pointing to the
installation root directory, the wellies' generated snippets will be

```python exec="true" id="systemvenv_env" result="shell"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
import pyflow as pf
from wellies.tools import parse_environment
tool = parse_environment(
    lib_dir="$LIB_DIR",
    name="datasets_env",
    options=dict(
        type="venv",
        packages=["anemoi_datasets"],
        depends=["python"]
    )
)
for tt in ['setup', 'load', 'unload']:
    print(f"--------{tt} script-----------")
    sc = tool.scripts[tt]
    lines = [sc]
    if isinstance(sc, pf.Script):
        lines=sc.generate_stub()
    elif isinstance(sc, list):
        lines=pf.Script.generate_list_scripts(sc)

    print('\n'.join(lines))
    print()
```

/// admonition | Note
    type: Note
the reserved name `packages` always refers to other tools of this type specified
within your configuration. For external packages use `extra_packages`.
///


### Conda environments

Conda environments can be defined in three ways:
- Existing system environment
- Built from a specification list
- Built from a specification file

The loading and unloading script snippets for all of them will be same. They
differ only on the way they are set up and this will be the focus here.

#### System environment

A system conda environment can be configured as

```yaml title="tools.yaml"
tools:
  environments:
    system_conda:
      type: conda
      environment: base
```

Considering there is `LIB_DIR` environment variable pointing to the
installation root directory, the wellies' generated snippets will be

```python exec="true" id="system_conda" result="shell"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
import pyflow as pf
from wellies.tools import parse_environment
tool = parse_environment(
    lib_dir="$LIB_DIR",
    name="system_conda",
    options=dict(
        type="conda",
        environment="base",
    )
)
for tt in ['setup', 'load', 'unload']:
    print(f"--------{tt} script-----------")
    sc = tool.scripts[tt]
    lines = [sc]
    if isinstance(sc, pf.Script):
        lines=sc.generate_stub()
    elif isinstance(sc, list):
        lines=pf.Script.generate_list_scripts(sc)

    print('\n'.join([l for l in lines if l is not None]))
    print()
```

#### Build with custom packages

To specify a conda environment that needs to be built within your workflow from
a list of packages specifications, a configuration file can look like:

```yaml title="tools.yaml"
tools:
  environments:
    myconda:
      type: conda
      packages: ["earthkit"]
      extra_packages: ["python==3.10", "pcraster>=4.3.0", "gdal"]
      conda_cmd: "mamba -c conda-forge"
```

Here we also changed the conda base command to use on setup to use the mamba
environment solver and to give priority to the conda-forge channel. This allows
you to use any valid extra option for your conda commands.

/// admonition | Note
    type: Note
the reserved name `packages` always refers to other tools of this type specified
within your configuration. For external packages use `extra_packages`
///

/// admonition | Warning
    type: warning
If provided, `extra_packages` must always be a list, even of one element
///

Considering there is `LIB_DIR` environment variable pointing to the
installation root directory, the wellies' generated snippets will be

```python exec="true" id="conda_pkgs" result="shell"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
import pyflow as pf
from wellies.tools import parse_environment
tool = parse_environment(
    lib_dir="$LIB_DIR",
    name="myconda",
    options=dict(
        type="conda",
        packages=["earthkit"],
        extra_packages=["python==3.10", "pcraster>=4.3.0", "gdal"],
        conda_cmd="mamba -c conda-forge"
    )
)
for tt in ['setup', 'load', 'unload']:
    print(f"--------{tt} script-----------")
    sc = tool.scripts[tt]
    lines = [sc]
    if isinstance(sc, pf.Script):
        lines=sc.generate_stub()
    elif isinstance(sc, list):
        lines=pf.Script.generate_list_scripts(sc)

    print('\n'.join([l for l in lines if l is not None]))
    print()
```

#### From file

Another common way to specify conda environment is through yml files. A valid
configuration to obtain such a file from the local filesystem is

```yaml title="tools.yaml"
tools:
  environments:
    myconda:
      type: conda
      env_file:
        type: copy
        source: /path/to/project
        files: env.yml
```

The `env_file` specification can be any valid `wellies.StaticData` entry. For
more details on the options available, please check the
[data types page](data_config.md).

Considering there is `LIB_DIR` environment variable pointing to the
installation root directory, the wellies' generated snippets will be

```python exec="true" id="conda_cpfile" result="shell"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
import pyflow as pf
from wellies.tools import parse_environment
tool = parse_environment(
    lib_dir="$LIB_DIR",
    name="myconda",
    options=dict(
        type="conda",
        env_file=dict(type="copy", source="/path/to/project", files="env.yml")
    )
)
for tt in ['setup', 'load', 'unload']:
    print(f"--------{tt} script-----------")
    sc = tool.scripts[tt]
    lines = [sc]
    if isinstance(sc, pf.Script):
        lines=sc.generate_stub()
    elif isinstance(sc, list):
        lines=pf.Script.generate_list_scripts(sc)

    print('\n'.join([l for l in lines if l is not None]))
    print()
```

### Custom Environments

Custom environment is a flexible alternative to generate any other type of environment. Supports
definition of `load`, `unload` and `setup` scripts or commands from the configuration files.

```yaml title="tools.yaml"
tools:
  environments:
    myenv:
        type: custom
        load: "/path/to/env/load.sh"
        unload: "unload_myenv"
```

The wellies' generated snippets for the custom environment will be

```python exec="true" id="custom_env" result="shell"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.tools import parse_environment
tool = parse_environment(
    lib_dir="$LIB_DIR",
    name="myenv",
    options=dict(type="custom", load="/path/to/env/load.sh", unload="unload_myenv")
)
for tt in ['setup', 'load', 'unload']:
    print(f"--------{tt} script-----------")
    sc = tool.scripts[tt]
    print(sc)
    print()
```
