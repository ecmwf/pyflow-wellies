# Log Archiving - Managing job outputs with ArchivedRepeatFamily

Operational suites that iterate over dates (or any repeat dimension) accumulate
large amounts of job output files. The
[ArchivedRepeatFamily][wellies.log_archiving.ArchivedRepeatFamily] helps manage
this by:

1. **Backing up** job output and job files to a separate directory after each
   task completes (via an automatic exit hook).
2. **Rotating** backed-up logs at the end of each repeat iteration.
3. Optionally **archiving** old iterations to long-term storage (e.g. ECFS)
   as compressed tarballs.

## Basic usage

An `ArchivedRepeatFamily` wraps a standard pyflow
[AnchorFamily][pyflow.AnchorFamily] with a repeat attribute and automatic log
management. You define it by providing a `repeat_options` dictionary that
specifies the repeat type and its parameters.

```python title="suite.py" exec="true" source="above" session="log_archive" id="log_archive_basic"
import pyflow as pf
from wellies.log_archiving import ArchivedRepeatFamily

repeat = dict(
    type="RepeatDate",
    name="YMD",
    start="2020-01-01",
    end="2020-01-31",
)

with pf.Suite("forecast", files=".") as suite:
    with ArchivedRepeatFamily(
        name="main",
        repeat_options=repeat,
        logs_backup="/scratch/logs/backup",  # (1)!
    ):
        pf.Task("fetch", script=["echo fetching data"])
        pf.Task("run_model", script=["echo running model"])

suite.generate_node()
```

1. `logs_backup` activates the log management. Without it, the family behaves
   like a regular repeat family with no log handling.

## What gets generated

When `logs_backup` is provided, the family automatically:

- Injects an **exit hook** into every task that copies `ECF_JOBOUT` and
  `ECF_JOB` to the backup directory after each task finishes.
- Adds a **`loop_logs`** task that runs after all other tasks complete,
  renaming the backup directory with the current repeat value to preserve
  logs from each iteration.

```python exec="true" session="log_archive" result="shell" id="log_archive_tree"
print(suite)
```

## With long-term archival

When `logs_archive` is also provided, an additional **`archive_logs`** task is
created. It compresses previous iterations into tarballs and uploads them to the
archive path (using `ecp` for ECFS storage), then cleans up local copies.


```python title="suite.py" exec="true" result="python" source="above" session="log_archive_full" id="log_archive_full"
import pyflow as pf
from wellies.log_archiving import ArchivedRepeatFamily

repeat = dict(
    type="RepeatDate",
    name="YMD",
    start="2020-01-01",
    end="2020-01-31",
)

with pf.Suite("forecast", files=".") as suite:
    with ArchivedRepeatFamily(
        name="main",
        repeat_options=repeat,
        logs_backup="/scratch/logs/backup",
        logs_archive="ec:/uid/logs/archive",  # (1)!
    ):
        pf.Task("fetch", script=["echo fetching data"])
        pf.Task("run_model", script=["echo running model"])
suite.generate_node()
print(suite)
```

1. `logs_archive` requires `logs_backup` to also be set — the archival task
   operates on the backed-up logs.

## Adding your own tasks and families

`ArchivedRepeatFamily` is a context manager just like any pyflow family. You can
nest tasks and families freely inside it — they all benefit from the automatic
log backup exit hook:

```python title="suite.py" exec="true" source="above" result="python" session="log_archive_nested" id="log_archive_nested"
import pyflow as pf
from wellies.log_archiving import ArchivedRepeatFamily

repeat = dict(
    type="RepeatDate",
    name="YMD",
    start="2020-06-01",
    end="2020-06-30",
)

with pf.Suite("production", files=".") as suite:
    with ArchivedRepeatFamily(
        name="main",
        repeat_options=repeat,
        logs_backup="/scratch/logs/backup",
    ):
        pf.Task("prepare", script=["echo prepare"])
        with pf.Family("forecast"):
            pf.Task("run", script=["echo forecast"])
            pf.Task("post", script=["echo postproc"])
        pf.Task("verify", script=["echo verify"])
suite.generate_node()
print(suite)
```

## Configuration variables

The following ecflow variables are set automatically by `ArchivedRepeatFamily`:

| Variable | Set when | Description |
|----------|----------|-------------|
| `LOGS_BACKUP` | `logs_backup` provided | Path where job files are backed up |
| `LOGS_ARCHIVE` | `logs_archive` provided | Remote archive path for compressed logs |

## How the exit hook works

The built-in exit hook runs in every task's cleanup phase and performs:

1. Resolves the backup directory from `LOGS_BACKUP`, mirroring the output
   directory structure.
2. Creates the backup directory if needed.
3. Copies the job output (`ECF_JOBOUT`) and job script (`ECF_JOB`) into it.

/// admonition | Combining with other exit hooks
    type: hint
You can pass additional exit hooks via the `exit_hook` parameter — they will be
combined with the log backup hook automatically:

```python
from wellies.scripts import ScriptLoader

email_hook = ScriptLoader().load("email_exit_hook.sh")

with ArchivedRepeatFamily(
    name="main",
    repeat_options=repeat,
    logs_backup="/scratch/logs/backup",
    exit_hook=[email_hook],  # Combined with the built-in log backup hook
):
    ...
```

See [Exit Hooks](exit_hook.md) for more on email notifications.
///
