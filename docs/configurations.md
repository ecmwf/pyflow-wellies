# Introduction

One the main features that wellies provides is the ability to configure many
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
need to be set up before the workflow starts. They are usually refered to as
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
