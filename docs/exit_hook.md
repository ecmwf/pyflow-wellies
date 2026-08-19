# Exit Hooks - Task completion notifications

**pyflow** supports `exit_hook` — shell code that runs in the task cleanup phase,
regardless of whether the task succeeded or failed. This is the natural place to
add notifications, log backups, or any post-execution housekeeping.

**wellies** ships a ready-to-use email notification exit hook
(`email_exit_hook.sh`) that sends formatted emails on task completion or failure.
It can be loaded using the [wellies.scripts.ScriptLoader][] and passed directly
to any [pyflow.Task][].

/// admonition | Note
    type: important
The email exit hook requires `pyflow>=3.7.0` otherwise there is no way to know, at
exit time, whether the task succeeded or failed. If you are using an older version
of pyflow, please upgrade to use this feature.
///

## Loading and using the email exit hook

The [ScriptLoader][wellies.scripts.ScriptLoader] loads packaged shell snippets
and returns a [pyflow.Script][] object that can be passed to the `exit_hook`
parameter of any task.

```python title="suite.py" exec="true" source="above" session="exit_hook" id="exit_hook_load"
import pyflow as pf
import wellies as wl
from wellies.scripts import ScriptLoader

# Load the packaged email exit hook
email_hook = ScriptLoader().load("email_exit_hook.sh")
```

## Attaching to a task

Pass the loaded script as the `exit_hook` parameter. The hook requires two
ecflow variables to be defined — `MAIL_TYPE` and `MAIL_USER` — which control
when and to whom notifications are sent.

```python title="suite.py" exec="true" source="above" session="exit_hook" id="exit_hook_task"
with pf.Suite(
    name="notify_suite",
    files=".",
    host=pf.LocalHost(),
    variables=dict(
        MAIL_TYPE="FAIL",           # (1)!
        MAIL_USER="ops@example.com" # (2)!
    ),
) as suite:

    task = pf.Task(
        name="process_data",
        script=["echo 'Processing data...'"],
        exit_hook=email_hook,  # (3)!
    )
```

1. `MAIL_TYPE` controls when emails are sent: `"ALL"` for every completion,
   `"FAIL"` for failures only.
2. `MAIL_USER` is the recipient email address.
3. The exit hook is appended to the task's cleanup section automatically by
   pyflow.

## Configuration variables

The email exit hook reads the following ecflow variables at runtime:

| Variable | Required | Description |
|----------|----------|-------------|
| `MAIL_TYPE` | Yes | When to send emails: `ALL` (always) or `FAIL` (only on non-zero exit) |
| `MAIL_USER` | Yes | Recipient email address |
| `ECF_NAME` | Auto | Task path (set by ecflow) |
| `ECF_HOST` | Auto | Server host (set by ecflow) |
| `ECF_TRYNO` | Auto | Attempt number (set by ecflow) |
| `ECF_JOB` | Auto | Job file path (set by ecflow) |
| `ECF_JOBOUT` | Auto | Job output path (set by ecflow) |

Variables marked **Auto** are provided by the ecflow framework and do not need
to be defined by the user.

## Email behaviour

The notification format depends on exit status:

- **Success** (`exit code 0`): plain-text email with subject
  `[SUCCESS] Job /path/to/task completed in attempt N`
- **Failure** (`exit code ≠ 0`): HTML email with subject
  `[ABORT] Job /path/to/task failed in attempt N`, including an extracted
  traceback from the job output file.

/// admonition | Hint
    type: hint
The hook uses `sendmail` for HTML emails and `mailx` for plain text. Ensure at
least one of these is available on the execution host.
///

## Applying the hook to multiple tasks

Since `MAIL_TYPE` and `MAIL_USER` are ecflow variables, they can be defined at
any node level (suite, family, or task). This makes it straightforward to enable
notifications for an entire subtree:

```python title="suite.py" exec="true" source="above" session="exit_hook" id="exit_hook_family"
with pf.Suite(
    name="production",
    files=".",
    host=pf.LocalHost(),
    variables=dict(MAIL_TYPE="FAIL", MAIL_USER="team@example.com"),
) as suite:

    with pf.Family("critical"):
        pf.Task("step1", script=["echo step1"], exit_hook=email_hook)
        pf.Task("step2", script=["echo step2"], exit_hook=email_hook)

    with pf.Family("optional"):
        # Override: no notifications for this family
        pf.Task(
            "cleanup",
            script=["echo cleanup"],
            exit_hook=email_hook,
            variables=dict(MAIL_TYPE=""),  # (1)!
        )
```

1. Setting `MAIL_TYPE` to an empty string effectively disables the hook for
   this task, since the guard condition requires a non-empty value.

## Combining multiple exit hooks

The `exit_hook` parameter accepts a list, allowing you to compose several hooks:

```python title="suite.py" exec="true" source="above" session="exit_hook" id="exit_hook_combine"
custom_hook = pf.Script(["echo 'Custom post-processing done'"])

pf.Task(
    name="multi_hook",
    script=["echo 'main work'"],
    exit_hook=[email_hook, custom_hook],  # Both run at cleanup
)
```

/// admonition | See also
    type: info
The [wellies.log_archiving.ArchivedRepeatFamily][] class automatically injects
its own exit hook for backing up job output files when `logs_backup` is
configured — an example of how exit hooks integrate with higher-level wellies
components.
///
