import pyflow as pf
from wellies.families import ArchivedRepeatFamily


def test_log_archive(tmpdir):
    repeat = {
        "name": "YMD",
        "type": "RepeatDate",
        "begin": "2020-01-01",
        "end": "2020-01-03",
    }
    with pf.Suite("s") as suite:
        with ArchivedRepeatFamily(
            "main", repeat, f"{tmpdir}/store", f"{tmpdir}/ecfs"
        ) as main:
            pf.Task("t1")
            with pf.Family("f1"):
                pf.Task("t2")

    children = main.executable_children
    for chld in children:
        assert chld._exit_hook == [main.exit_hook()]
    suite.generate_node()
    tasks = suite.all_tasks
    assert len(tasks) == 4
