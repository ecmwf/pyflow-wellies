import pyflow as pf
import pytest

import wellies as wl


@pytest.mark.parametrize("contextname", ["serial", "parallel"])
def test_ecfvarstask_creation(wlhost, contextname):
    with pf.Suite("s1", host=wlhost.host):
        t1 = wl.EcfResourcesTask(
            name="t1",
            submit_arguments=wlhost.host.submit_arguments[contextname],
        )

    assert t1.name == "t1"
    task_variable_names = [v.name for v in t1.variables]
    task_variable_values = [v.value for v in t1.variables]
    for k, v in wlhost.host.submit_arguments[contextname].items():
        assert k.upper() in task_variable_names
        assert v in task_variable_values


@pytest.mark.parametrize("contextname", ["serial", "parallel"])
def test_ecfvarstask_creation_parentlookup(wlhost, contextname):
    slurmhost = wlhost.host
    default_vars = wlhost.defaults
    with pf.Suite("s1", host=slurmhost):
        with pf.Family("f1", variables=default_vars):
            t1 = wl.EcfResourcesTask(
                name="t1",
                submit_arguments=slurmhost.submit_arguments[contextname],
            )

    assert t1.name == "t1"
    keynames = [
        k.upper() for k in slurmhost.submit_arguments[contextname].keys()
    ]
    keyvals = list(slurmhost.submit_arguments[contextname].values())
    for var in t1.variables:
        assert var.name in keynames
        assert var.value in keyvals
        assert var.name not in default_vars.keys()

    for var in t1.parent.variables:
        assert var.name in default_vars.keys()
        assert var.value == default_vars[var.name]


@pytest.mark.parametrize("contextname", ["serial", "parallel"])
def test_ecfvarstask_creation_host_submitargs(wlhost, contextname):
    with pf.Suite("s1", host=wlhost.host):
        t1 = wl.EcfResourcesTask(
            name="t1",
            submit_arguments=contextname,
        )

    assert t1.name == "t1"
    task_variable_names = [v.name for v in t1.variables]
    task_variable_values = [v.value for v in t1.variables]
    for k, v in wlhost.host.submit_arguments[contextname].items():
        assert k.upper() in task_variable_names
        assert v in task_variable_values


@pytest.mark.parametrize("contextname", ["serial", "parallel"])
def test_ecfvarstask_creation_host_submitargs_parentvars(wlhost, contextname):
    slurmhost = wlhost.host
    default_vars = wlhost.defaults
    with pf.Suite("s1", host=slurmhost):
        with pf.Family("f1", variables=default_vars):
            t1 = wl.EcfResourcesTask(
                name="t1",
                submit_arguments=contextname,
            )

    assert t1.name == "t1"
    keynames = [
        k.upper() for k in slurmhost.submit_arguments[contextname].keys()
    ]
    keyvals = list(slurmhost.submit_arguments[contextname].values())
    for var in t1.variables:
        assert var.name in keynames
        assert var.value in keyvals
        assert var.name not in default_vars.keys()

    for var in t1.parent.variables:
        assert var.name in default_vars.keys()
        assert var.value == default_vars[var.name]
