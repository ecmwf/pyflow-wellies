# Introduction

One of the main features that wellies provides is the ability to configure many
aspects of suite definition through *YAML* files. We recommend splitting the full
configuration in 4 different files, each containing independent components and following the general convention:

1. **Main configuration**: Here we define the general suite options like where to write
generated scripts, the execution host, where to write outputs and any other specific
option for the workflow. This can be any yaml file, but if using `wellies-quickstart`
templating there are some defaults defined. Please refer to the
[quickstart guide](quickstart_guide.md) for details.
2. **Tools** configuration: Here we can define different softwares, their dependencies
and execution environments that any of the tasks in the workflow can refer to.
3. **Execution contexts** configuration: Here we can define different set of options  
for the submission system that tasks can refer to. If using a direct execution
host like [pyflow.SSHHost][] or [pyflow.LocalHost][] this becomes irrelevant.
4. **Static data** configuration: Here we can define different external data sources that
need to be set up before the workflow starts. They are usually referred to as
`static data` as they are retrieved on setup time and used in read-only mode
throughout the suite. This is optional and depending on each use-case other setups can be more meaningful.

## YAML-templating

To simplify and make configuration files more flexible and reusable, wellies
provide a very simple templating system to write configuration files. Features are presented in the example below:

```yaml title="config.yaml"
suite_name: mysuite
user: "{USER}"  # (2)!

ecflow_server:
    hostname: localhost
    user: "{user}"
    deploy_dir: /home/username/{suite_name}  # (1)!

exectime_variable: "${ENVVAR}"  # (3)!

filename_template: "/path/to/file/{{fc_date}}"  # (4)!
```

1. The basic use is to provide variable substitution within a file using basic python
   string templating, here for main label `suite_name`.
2. There are some global template variables automatically derived from the
   system. Note the capitalized reference. For a full list, check [here](#global-template-variables)
3. Variables (bash or ecFlow) defined only on the task run environment can be referenced and will
   be ignored by the substitution algorithm
4. To escape the curly-brackets to use defined python template values that can
   be rendered in runtime, just double the brackets


The variable substitution algorithm will render the *YAML* file as a python
dictionary like:

```python
{
    "suite_name": "mysuite",
    "user": "username",
    "ecflow_server": {
        "hostname": "localhost",
        "user": "username",
        "deploy_dir": "/home/username/mysuite",
    },
    "exectime_variable": "${ENVVAR}"
    "filename_template": "/path/to/file/{fc_date}",
}
```

### Scoping rules

Keys are resolved in the order they appear (top-level first, then nested mappings).
Each nested mapping is given a **snapshot** of the substitution context that was built
up to that point — it can reference any top-level key defined before it, but its own
keys do **not** propagate back to the parent scope or to sibling mappings.

```yaml title="scoping_example.yaml"
name: global                # (1)!
nested_a:
    name: local             # (2)!
    path: /vol/{name}       # (3)!
nested_b:
    path: /scratch/{name}   # (4)!
top_path: /data/{name}      # (5)!
```

1. Top-level key available to everything.
2. This shadows `name` only **inside** `nested_a`; it does not affect other scopes, but can be used within `nested_a`.
3. Resolves to `/vol/local` — uses value within scope: `nested_a.name`.
4. Resolves to `/scratch/global`.
5. Resolves to `/data/global`.

/// admonition | Note
    type: note

A key defined inside a nested mapping (e.g. `nested_a.name`) is **not** visible
outside that mapping. If a top-level `{...}` reference cannot be resolved from
the top-level keys, substitution raises a `KeyError` — even if a nested mapping
happens to define a key with the same name.
///

### Global template variables

As a shortcut, access to some common system-wide variables is made available on  
wellies and can be used anywhere in any configuration file.

```python exec="true" id="get-uservars" linenums="1"
import os, sys, getpass
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.config import get_user_globals
current_user=getpass.getuser()
varnames=get_user_globals()
varnames={ k: v.replace(current_user, 'username') for k,v in varnames.items()}
varnames["PWD"]="/current/working/directory"
pretty='\n'.join([f"{k}: '{v}'" for k,v in varnames.items()])
print(f"```\n{pretty}\n```")
```

/// admonition | Attention
    type: warning

With `pyflow-wellies` <= 1.1.0 if one of the global variables is not defined, the substitution happens with
an empty string. This can lead to unexpected results, specially when building system paths. In newer versions,
the substitution will raise an error if the variable is not defined and used in one of the configuration files.
///

In the following pages the specifics for other wellies' components will be
detailed.

## Special keys

In this section, reserved keys that have a special meaning in the configuration files are described.

### ecflow_variables
This key is used to define one-level mapping for variables that will be defined at the ecFlow suite level.
It is special because it can be defined in any of the configuration files, but it will be merged into the main configuration file
when the suite is built, allowing for more contextualised definition of variables.

It is important to note that, due to this behaviour and unlike with other keys or configuration entries
(where an error is raised), any duplication just overwrites the previous value. Therefore, the order of
parsing configuration files may alter the final mapping of variables in the presence of duplicates.

/// admonition | Note
    type: note

For ordinary (non-`ecflow_variables`) keys, duplicate detection treats a `null`
value the same as any other value: if a key is present in an earlier file — even
with a `null` value — redefining it in a later file raises a `KeyError`.
///

/// admonition | Note
    type: note

`ecflow_variables` are merged from all configuration files and substituted last,
after every other configuration key. Because of this ordering, a variable's value
can reference any top-level configuration key with `{...}` templating, regardless
of which file defined it.

Within the merged `ecflow_variables` mapping, entries are resolved in insertion
order. An entry can reference an earlier entry in the same mapping, but forward
references (referencing a key defined later) will raise a `KeyError`.

The reverse is not supported: other configuration values cannot reference an
`ecflow_variable` with `{...}` templating. To use an `ecflow_variable` in another
value, use the ecFlow runtime form `${VAR:-default}`, which is expanded when the
suite runs.

Nested keys defined elsewhere in the configuration are **not** visible inside
`ecflow_variables` substitution (see [Scoping rules](#scoping-rules)).
Duplicate variable names across files resolve last-wins.
///

Considering we have the following two configuration files:

````yaml title="config.yaml"
host: localhost
ecflow_server:
    hostname: localhost
    user: username
ecflow_variables:
    EXPVER: "001"
````

````yaml title="tools.yaml"
ecflow_variables:
    MODULES_VERSION: "latest"
tools:
    modules:
        python:
            version: "${MODULES_VERSION:-default}"
````

```python exec="true" session="merged_variables" id="write_example_files_merged_variables"
import os, tempfile
tmpdirname = tempfile.mkdtemp()
with open(f"{tmpdirname}/tools.yaml", 'w') as ftools:
    ftools.write('ecflow_variables:\n    MODULES_VERSION: "latest"\ntools:\n    modules:\n        python:\n            version: "${MODULES_VERSION:-default}"\n')
with open(f"{tmpdirname}/config.yaml", 'w') as fconfig:
    fconfig.write("host: localhost\necflow_server: \n    hostname: localhost\n    user: username\necflow_variables:\n    EXPVER: '001'\n")
```

We can see that the `ecflow_variables` key is defined in both files, but
the final mapping of variables will be flat and ready to be passed to any `Node` `variables` attribute

```python exec="true" id="ecflow_variables-merge-example" source="above" result="python" session="merged_variables"
import wellies as wl
import os; curdir=os.getcwd(); os.chdir(tmpdirname)  # markdown-exec: hide
import pprint
options = wl.parse_yaml_files(["config.yaml", "tools.yaml"])
os.chdir(curdir)  # markdown-exec: hide
pp = pprint.PrettyPrinter(indent=2, sort_dicts=False, width=40)  # markdown-exec: hide
options = pp.pformat(options)  # markdown-exec: hide
print(options)
```
