from importlib.resources import files
from pkgutil import get_data

import pyflow as pf
import pytest

from wellies.scripts import ScriptLoader


def test_script_loader_loads_exit_hook_script():
    lines = ScriptLoader().load("exit_hook.sh")

    assert isinstance(lines, list)
    assert lines
    assert any("EXIT_STATUS" in line for line in lines)
    assert any("mailx -s" in line for line in lines)


def test_script_loader_supports_alternate_subdir():
    lines = ScriptLoader(subdir="templates").load("build.sh_t")

    assert isinstance(lines, list)
    assert lines


def test_script_loader_missing_resource_raises():
    with pytest.raises(FileNotFoundError):
        ScriptLoader().load("does-not-exist.sh")


def test_script_loader_e2e_with_pyflow_task():
    script_lines = ScriptLoader().load("exit_hook.sh")

    with pf.Suite("s1") as suite:
        task = pf.Task("notify", script=script_lines)

    suite.generate_node()
    rendered_script = task.script.value

    assert "EXIT_STATUS" in rendered_script
    assert "sendmail -t" in rendered_script


def test_packaged_script_discoverable_with_importlib_resources():
    resource = files("wellies").joinpath("scripts", "exit_hook.sh")

    assert resource.is_file()
    assert "EXIT_STATUS" in resource.read_text()


def test_packaged_script_discoverable_with_pkgutil():
    data = get_data("wellies", "scripts/exit_hook.sh")

    assert data is not None
    assert b"EXIT_STATUS" in data
