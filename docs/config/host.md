# Host - Managing task submission arguments

**pyflow** defines a [Host][pyflow.Host] object to supply the necessary submission arguments
for task level execution within ecflow suites. It defines different extensible
[host types](https://pyflow-workflow-generator.readthedocs.io/en/latest/content/introductory-course/host-management.html#Existing-Host-Classes). Especially for executions within a
queueing system, there are many options on how to submit jobs. **pyflow**
chooses to delegate all properties that determine the execution process to the
`Host`, but those are also features and requirements of each particular `Task`.
For more on this topic, please check pyflow's
[job characteristics](https://pyflow-workflow-generator.readthedocs.io/en/latest/content/introductory-course/host-management.html#Job-Characteristics).
**wellies** offers a higher level `Host` class that allows simpler configuration to shorten this
gap. It's mainly useful for easy interoperability of the workflow (or parts of it) on different execution environments, either local or
remote HPC-like machines.

The main idea is to group every aspect that is bound to the context on which each task is to run,
and being able to provide to a `Task` specific `submit_arguments` options
that will serve the `Host` it's going to be executed on.

## Basic use

A `host` entry is defined by the following parameters:
- `hostname`: the name of the host where the tasks will run. This can be a
  remote host or a local one.
- `user`: the user name to use when dealing with the host. If remote the user must have access to the host
  by `hostname` via any protocol it is defined to use, e.g `ssh`.

Optionally, a `host` entry can define the following parameters:
- `ecflow_path`: The path to the ecflow_client executable on `hostname`. If None, try to get from the current `PATH` where the `ecflow_client` must be present. Defaults to None.
- `server_ecfvars`: Whether to use **server-side** ECF_ variables. This will make pyflow to not define the variables: `ECF_JOB_CMD`, `ECF_CHECK_CMD`, `ECF_KILL_CMD` and `ECF_STATUS_CMD`. Defaults to `False`.
- `extra_variables`: Mapping of additional ecflow variables to set on the host.
- `submit_arguments`: a dictionary with the submission arguments to be used by the `Host` when submitting tasks.
  This is an extensible mapping that can be used to define different sets of
  submission options for different tasks that can run on a particular `host`.
  The actual list of valid options, depend on the `Host` object that will be
  used, but nothing blocks one to create `Host`-specific mappings to handle different arguments.

The configuration can also provide any valid option for a [pyflow.Host](https://pyflow-workflow-generator.readthedocs.io/en/latest/content/introductory-course/host-management.html#Host-Arguments) object, the most common ones are:
- `log_directory`: the path, in `hostname` where job output files will be stored. Must be accessible by the user
  defined in `user`. It will define the top-level `ECF_OUT` variable. It can point to a custom or generated ecFlow variable.
- `workdir`: the path, in `hostname` where the tasks will primarily run. Usually, `pyflow` will add commands
  to create and change the directory to this path at the preamble of every task script. It can point to an ecFlow variable.


In the following examples, we will focus on valid options for a [pyflow.SLURMHost][] that uses the `Slurm` submission system.
In a `submit_arguments` configuration entry, you can define different
groups of submission options to be use for different tasks that can run on a particular `host`.

```yaml title="host.yaml"
host:
    hostname: "my.slurm.cluster"
    user: "a_username"
    log_directory: "%ECF_HOME%"
    workdir: "$TMPDIR"
    submit_arguments:
        serial:
            queue: nf
            total_tasks: 1
            memory_per_cpu: 4Gb
        small_parallel:
            queue: nf
            total_tasks: 16
            memory_per_cpu: 2Gb
```

The `host` configuration above, can be directly interfaced with [wellies.get_host][] that will return a
valid `pyflow.Host`object and a list of submission-related ecFlow variables mappping that can be defined at
a particular node level or not, depending on the design of the workflow.

```python title="config.py" exec="true" source="above" session="submit_args" id="basic_host_config"
import pyflow as pf
import wellies as wl

host, submit_variables = wl.get_host(
    hostname="my.slurm.cluster",
    user="a_username",
    log_directory="%ECF_HOME%",
    workdir="$TMPDIR",
    submit_arguments=dict(
        serial=dict(queue='nf', total_tasks=1, memory_per_cpu="4gb"),
        small_parallel=dict(queue='nf', total_tasks=4, memory_per_cpu="2gb")
    ),
)
```

In the `Task` definition code, you can pass those parsed dictionaries
directly to a `Task` object, or refer to them by name in the `submit_arguments`
parameter. The `Task` will then use the `Host` object to generate the appropriate
`Slurm` headers for the task script.

```python title="suite.py" exec="true" source="above" session="submit_args" id="basic_host_config_suite"

with pf.Suite(
    name="mysuite",
    files=".",
    host=pf.SLURMHost(  #(1)!
        name='cluster',
        user="username",
        ecflow_path="/path/to/ecflow/at/server",
        submit_arguments=host.submit_arguments,
        extra_variables=submit_variables,  #(2)!
    )
):

    t1 = pf.Task(
        name='t1',
        submit_arguments='serial',  #(3)!
        script=["echo 'Hello from t1'"],
    )
    t2 = pf.Task(
        name='t2',
        submit_arguments='small_parallel',
        script=["parallel -j $TASKS echo 'Hello from t2-{%}' ::: A B C D E"],
    )
```

1. The `Host` can be defined for any node. In this simple case we are expecting
to run everything on the same one, therefore defining it at the suite level.
This will, among a few other things, define the Ecflow variables `ECF_JOB_CMD`,
`ECF_KILL_CMD` at that node level.
2. The `extra_variables` parameter is used to pass the parsed
`submit_variables` dictionary to the `Host`. This will define extra Ecflow variables
`QUEUE`, `TASKS`, `ECF_QUEUE`, `MEMORY_PER_TASK` that will be available for any task running on that host.
3. A Task will receive `Host` specific options for its execution through the `submit_arguments` parameter, here a direct reference by name of the configuration entry.

The full **pyflow** generated script for each task will contain the appropriate
`Slurm` headers.

**t1**
```python exec="true" title="t1.ecf" session="submit_args" result="shell" id="basic_host_config_t1"
script, includes = t1.generate_script()
script = '\n'.join(script[:6])
print(f"{script}")
print("(...)")
```

**t2**
```python exec="true" title="t2.ecf" session="submit_args" result="shell" id="basic_host_config_t2"
script, includes = t2.generate_script()
script = '\n'.join(script[:6])
print(f"{script}")
print("(...)")
```

## Using defaults and the wellies parser

In a `submit_arguments` configuration entry, `defaults` is a reserved key. If
present, its entries will be passed to every other submission arguments entry
to form a complete and self-sufficient list of options for each entry as in the example below.

```yaml title="host.yaml"
host:
    hostname: "my.slurm.cluster"
    user: "a_username"
    submit_arguments:
        defaults:
            job_name: "%FAMILY1:NOT_DEF%_%TASK%"
            queue: nf
        serial:
            total_tasks: 1
            memory_per_cpu: 4Gb
            tmpdir_size: 10Gb
        small_parallel:
            total_tasks: 16
            memory_per_cpu: 2Gb
            tmpdir_size: 20Gb
```

Will result in the following parsed options dictionary:

```python exec="true" session="submit_args_defaults" result="python" id="submit_args_defaults"
import pyflow as pf
import wellies as wl

host, submit_variables = wl.get_host(
    hostname="my.slurm.cluster",
    user="a_username",
    submit_arguments=dict(
        defaults=dict(job_name="%FAMILY1:NOT_DEF%_%TASK%",queue='nf'),
        serial=dict(total_tasks=1, memory_per_cpu="4gb", tmpdir_size="10gb"),
        small_parallel=dict(total_tasks=16, memory_per_cpu="2gb", tmpdir_size="20gb"),
    ),
)
print(host.submit_arguments)
```

## Submission arguments as Ecflow variables

/// admonition | Hint
    type: hint
This feature is a shortcut (or a hack) that should be used with care. It is
recommended that only variables that should be tweaked by operators during the
workflow execution should be elevated to Ecflow variables.

It might be more flexible to have template variables at a task script level
that can be tweaked by a simple script regeneration step than having to
replace a complex running node because some variable value just changed.
///

You can notice above that [wellies.get_host][] returns two
values. We used the defined `host`, among other things, to control each task's
`submit_arguments` parameter. The second returned value is a dictionary
with a direct translation of any key:value mapping in a format ready to be used as node
variables. Which node should receive it, is a design decision and we will leave
open for the developer to decide.

With the configuration example above, the variables dictionary will be:

```python exec="true" session="submit_args" result="python"
print("defaults =", submit_variables)
```

If you decide to add some common submission options as Ecflow variables to one
of your suite's node you would need to add them for each task. **wellies**
provides the [wellies.tasks.EcfResourcesTask][] class to help with that.

In the example below, we use the `submit_variables` dictionary returned from the parsing
function to define suite level variables. A `EcfResourcesTask` will transform
all options from its `submit_arguments` to Ecflow variables. Additionally, it
will inspect its own parents for variables matching in name **and** value
to use instead of defining new ones.


```python title="suite.py" exec="true" source="above" result="shell" session="submit_args_defaults" id="submit_args_defaults_suite"
from wellies.tasks import EcfResourcesTask

with pf.Suite(
    name="mysuite",
    files=".",
    host=host,
    variables=submit_variables,  #(1)!
) as mysuite:

    t1 = EcfResourcesTask(
        name='t1',
        submit_arguments=host.submit_arguments['serial'],  #(2)!
    )
    t2 = EcfResourcesTask(
        name='t2',
        submit_arguments=host.submit_arguments['small_parallel'],
    )

print(mysuite)
```

1. We simply pass `submit_variables` dictionary as a `variables` parameter. This can be
done on any node. Where to define it, is a design decision.
2. Using the `submit_arguments` configuration entry does not change. Everything
happens in the task initialiser.

Task *t2* `Slurm` headers will be modified to receive values from Ecflow
variables. Following Ecflow framework, these will be replaced just before
submission when the actual job file is written. The values are well defined
for each task in the suite definition, either at task level or above, like
`JOB_NAME`.

```python exec="true" session="submit_args_defaults" result="shell" id="submit_args_defaults_t2"
script, includes = t2.generate_script()
script = '\n'.join([l for l in script if l.startswith('#SBATCH')])
print("(...)")
print(f"{script}")
print("(...)")
```

Now, if we want to add a third task that uses the same `submit_arguments` as
`t1` we would have many similar variables defined for each task. This will grow
out of control quite easily. That's where the parent inspection feature comes
at help.

```python title="suite.py" exec="true" source="above" result="shell" session="submit_args_defaults" id ="submit_args_defaults_suite_variables"
from wellies.tasks import EcfResourcesTask

with pf.Suite(
    name="mysuite",
    files=".",
    host=host,
    variables=submit_variables,
) as mysuite:

    with pf.Family(name='f1', variables=dict(TMPDIR_SIZE='10gb')) as n_f1:  #(1)!
      t1 = EcfResourcesTask(
          name='t1',
          submit_arguments=host.submit_arguments['serial'],
      )
      t2 = EcfResourcesTask(
          name='t2',
          submit_arguments=host.submit_arguments['small_parallel'],  #(2)!
      )
      t3 = EcfResourcesTask(
          name='t3',
          submit_arguments=host.submit_arguments['serial'],  #(3)!
      )

print(mysuite)
```

1. We define the common variable on a higher level node, a family `f1`.
2. *t2* still uses a different value for the `TMPDIR_SIZE` option. As those won't
match, the variable is still defined for *t2*.
3. *t3* will use the same type of resources that *t1*, so it's reasonable to
imagine that those can be managed together.

All tasks headers will remain the same, referring to Ecflow variables for its
variables.

```python exec="true" title="t1.ecf" session="submit_args_defaults" result="shell" id="submit_args_defaults_suite_variables_t1"
script, includes = t1.generate_script()
script = '\n'.join([l for l in script if l.startswith('#SBATCH')])
print("(...)")
print(f"{script}")
print("(...)")
```
