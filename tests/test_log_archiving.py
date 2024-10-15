import pyflow as pf
import pytest

from wellies.log_archiving import ArchivedRepeatFamily


@pytest.mark.parametrize(
    "backup, hook, num_tasks",
    [
        ["backup", True, 4],
        [None, False, 2],
    ],
)
def test_log_archive(tmpdir, backup, hook, num_tasks):
    repeat = {
        "name": "YMD",
        "type": "RepeatDate",
        "start": "2020-01-01",
        "end": "2020-01-03",
    }
    with pf.Suite("s", files=str(tmpdir)) as suite:
        with ArchivedRepeatFamily("main", repeat, backup, backup) as main:
            pf.Task("t1")
            with pf.Family("f1"):
                pf.Task("t2")

    assert bool(main.exit_hook()) == hook
    suite.generate_node()
    tasks = suite.all_tasks
    assert len(tasks) == num_tasks
