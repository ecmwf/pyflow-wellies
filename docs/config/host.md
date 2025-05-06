# Host - Managing task submission arguments

**pyflow** defines a [Host][pyflow.Host] object to supply the necessary submission arguments
for task level execution within ecflow suites. It defines different extensible
[host types](https://pyflow-workflow-generator.readthedocs.io/en/latest/content/introductory-course/host-management.html#Existing-Host-Classes). Specially for executions within a
queueing system, there are many options on how to submit jobs. **pyflow**
chooses to delegate all properties that determine the execution process to the
`Host`, but those are also features and requirements of each particular `Task`.
For more on this topic, please check pyflow's
[job characteristics](https://pyflow-workflow-generator.readthedocs.io/en/latest/content/introductory-course/host-management.html#Job-Characteristics)

**wellies** offers the `submit_arguments` configuration option to shorten this
gap. It's mainly useful for HPC execution environments to handle job options
single or multi-Host suites.

The main idea is to provide to the `Task`, specific `submit_arguments` options
that will serve to one or many `Host`'s it's going to be executed on.

The actual list of valid options, depend on the `Host` object that will be
used, but nothing blocks one to create `Host`-specific mappings to handle different arguments. Here we will focus on options valid for a
[pyflow.SLURMHost][] that uses `Slurm` submission system.

## Basic use

In a `submit_arguments` configuration entry, you can define different
groups of submission options to be use for different tasks.

```yaml title="host.yaml"
host:
    hostname: "localhost"
    user: "a_username"
    job_out: "%ECF_HOME%"
    workdir: "$TMPDIR"
    submit_arguments:
        serial:
            queue: nf
            tasks: 1
            memory_per_task: 4Gb
        small_parallel:
            queue: nf
            tasks: 16
            memory_per_task: 2Gb
```

Skipping the file handling part, the submit arguments values can be rendered into a Python
object like

```python title="config.py" exec="true" source="above" session="submit_args"
import pyflow as pf
import wellies as wl

arguments, defaults = wl.parse_submit_arguments(dict(
    serial=dict(queue='nf', tasks=1, memory_per_task="4gb"),
    small_parallel=dict(queue='nf', tasks=16, memory_per_task="2gb"),
))
```

In the `Task` definition code, you can pass those parsed dictionaries
directly to a `Task` object.

```python title="suite.py" exec="true" source="above" session="submit_args"

with pf.Suite(
    name="mysuite",
    files=".",
    host=pf.SLURMHost(  #(1)!
        name='cluster',
        user="username",
        ecflow_path="/path/to/ecflow/at/server"
    )
):

    t1 = pf.Task(
        name='t1',
        submit_arguments=submit_arguments['serial'],  #(2)!
        script=["echo 'Hello from t1'"],
    )
    t2 = pf.Task(
        name='t2',
        submit_arguments=submit_arguments['small_parallel'],
        script=["echo 'Hello from t2'"],
    )
```

1. The `Host` can be defined for any node. In this simple case we are expecting
to run everything on the same one, therefore defining it at the suite level.
This will, among a few other things, define the Ecflow variables `ECF_JOB_CMD`,
`ECF_KILL_CMD` at the node level.
2. A Task will receive `Host` specific options for its execution through the `submit_arguments` parameter, here a direct translation from a configuration
file.

The full **pyflow** generated script for each task will contain the appropriate
`Slurm` headers.

**t1**
```python exec="true" title="t1.ecf" session="submit_args" result="shell"
script, includes = t1.generate_script()
script = '\n'.join(script[:6])
print(f"{script}")
print("(...)")
```

**t2**
```python exec="true" title="t2.ecf" session="submit_args" result="shell"
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
submit_arguments:
  defaults:
    job_name: "%FAMILY1:NOT_DEF%_%TASK%"
    queue: nf
  serial:
    tasks: 1
    memory_per_task: 4Gb
    tmpdir: 10Gb
  small_parallel:
    tasks: 16
    memory_per_task: 2Gb
    tmpdir: 20Gb
```

Will result the following parsed options dictionary:

```python exec="true" session="submit_args" result="python"

submit_arguments, defaults = wl.parse_submit_arguments(dict(
    defaults=dict(job_name="%FAMILY1:NOT_DEF%_%TASK%",queue='nf'),
    serial=dict(tasks=1, memory_per_task="4gb", tmpdir="10gb"),
    small_parallel=dict(tasks=16, memory_per_task="2gb", tmpdir="20gb"),
))

print(submit_arguments)
```

## Submission arguments as Eclow variables

/// admonition | Hint
    type: hint
This feature is a shortcut (or a hack) that should be used with care. It is
recommended that only variables that should be tweaked by operators during the
workflow execution should be elevated to Ecflow variables.

It might be more flexible to have template variables at a task script level
that can be tweaked by a simple script regeneration step than having to
replace a complex running node because some variable value just changed.
///

You can notice above that [wellies.parse_submit_arguments][] returns two
values. We used the first one to define each task's `submit_arguments`
parameter. The second returned value is another dictionary with a direct
translation of any `defaults` values in a format ready to be used as node
variables. Which node should receive it, is a design decision and we will leave
open for the developer to decide.

With the configuration example above, the variable defaults dictionary will be:

```python exec="true" session="submit_args" result="python"
print("defaults =", defaults)
```

If you decide to add some common submission options as Ecflow variables to one
of your suite's node you would need to add them for each task. **wellies**
provides the [wellies.tasks.EcfResourcesTask][] class to help with that.

In the example below, we use the `defaults` dictionary returned from the parsing
function to define suite level variables. A `EcfResourcesTask` will transform
all options from its `submit_arguments` to Ecflow variables. Additionally, it
will inspect its own parents for variables matching in name **and** value
to use instead of defining new ones.


```python title="suite.py" exec="true" source="above" result="shell" session="submit_args"
from wellies.tasks import EcfResourcesTask

with pf.Suite(
    name="mysuite",
    files=".",
    host=pf.SLURMHost(
        name='cluster',
        user="username",
        ecflow_path="/path/to/ecflow/at/server",
    ),
    variables=defaults,  #(1)!
) as mysuite:

    t1 = EcfResourcesTask(
        name='t1',
        submit_arguments=submit_arguments['serial'],  #(2)!
    )
    t2 = EcfResourcesTask(
        name='t2',
        submit_arguments=submit_arguments['small_parallel'],
    )

print(mysuite)
```

1. We simply pass `defaults` dictionary as a `variables` parameter. This can be
done on any node. It is a design decision.
2. Using the `submit_arguments` configuration entry does not change. Everything
happens in the tast initializer.

Task *t2* `Slurm` headers will be modified to receive values from Ecflow
variables. Following Ecflow framework, these will be replaced just before
submission when the actual job file is written. The values are well defined
for each task in the suite definition, either at task level or above, like
`JOB_NAME`.

```python exec="true" session="submit_args" result="shell"
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

```python title="suite.py" exec="true" source="above" result="shell" session="submit_args"
from wellies.tasks import EcfResourcesTask

with pf.Suite(
    name="mysuite",
    files=".",
    host=pf.SLURMHost(
        name='cluster',
        user="username",
        ecflow_path="/path/to/ecflow/at/server",
    ),
    variables=defaults,
) as mysuite:

    with pf.Family(name='f1', variables=dict(SSDTMP='10gb')) as n_f1:  #(1)!
      t1 = EcfResourcesTask(
          name='t1',
          submit_arguments=submit_arguments['serial'],
      )
      t2 = EcfResourcesTask(
          name='t2',
          submit_arguments=submit_arguments['small_parallel'],  #(2)!
      )
      t3 = EcfResourcesTask(
          name='t3',
          submit_arguments=submit_arguments['serial'],  #(3)!
      )

print(mysuite)
```

1. We define the common variable on a higher level node, a family `f1`.
2. *t2* still uses a different value for the `SSDTMP` option. As those won't
match, the variable is still defined for *t2*.
3. *t3* will use the same type of resources that *t1*, so it's reasonable to
imagine that those can be managed together.

All tasks headers will remain the same, referring to Ecflow variables for its
variables.

```python exec="true" title="t1.ecf" session="submit_args" result="shell"
script, includes = t1.generate_script()
script = '\n'.join([l for l in script if l.startswith('#SBATCH')])
print("(...)")
print(f"{script}")
print("(...)")
```
