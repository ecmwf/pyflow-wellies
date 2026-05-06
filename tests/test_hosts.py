from dataclasses import fields

import pyflow as pf
import pytest

from wellies.hosts import HOST_DEFAULTS
from wellies.hosts import EcflowServer
from wellies.hosts import get_host
from wellies.hosts import local_host

# ---------------------------------------------------------------------------
# Host type fixtures — each returns a dict of get_host() kwargs
# ---------------------------------------------------------------------------

HOST_CONFIGS = {
    "localhost": dict(
        hostname="localhost",
        user="testuser",
        ecflow_path="/usr/bin",
        expected_class=pf.LocalHost,
    ),
    "troika": dict(
        hostname="troika:hpc-cluster",
        user="testuser",
        ecflow_path="/usr/bin",
        expected_class=pf.TroikaHost,
    ),
    "slurm": dict(
        hostname="slurm:hpc-slurm",
        user="testuser",
        ecflow_path="/usr/bin",
        expected_class=pf.SLURMHost,
    ),
    "pbs": dict(
        hostname="pbs:hpc-pbs",
        user="testuser",
        ecflow_path="/usr/bin",
        expected_class=pf.PBSHost,
    ),
    "ssh": dict(
        hostname="ssh:hpc-ssh",
        user="testuser",
        ecflow_path="/usr/bin",
        expected_class=pf.SSHHost,
    ),
}


def _make_host(config, **overrides):
    """Call get_host with a HOST_CONFIGS entry, stripping test metadata."""
    kw = {k: v for k, v in config.items() if k != "expected_class"}
    kw.update(overrides)
    return get_host(**kw)


@pytest.fixture(params=HOST_CONFIGS.keys())
def host_config(request):
    """Parametrized fixture yielding each host type config."""
    return HOST_CONFIGS[request.param]


@pytest.fixture
def localhost_config():
    return HOST_CONFIGS["localhost"]


@pytest.fixture
def troika_config():
    return HOST_CONFIGS["troika"]


@pytest.fixture
def slurm_config():
    return HOST_CONFIGS["slurm"]


@pytest.fixture
def pbs_config():
    return HOST_CONFIGS["pbs"]


@pytest.fixture
def ssh_config():
    return HOST_CONFIGS["ssh"]


# ---------------------------------------------------------------------------
# EcflowServer dataclass
# ---------------------------------------------------------------------------


class TestEcflowServer:

    def test_required_fields(self):
        server = EcflowServer(
            hostname="ecflow-server", user="admin", deploy_dir="/deploy"
        )
        assert server.hostname == "ecflow-server"
        assert server.user == "admin"
        assert server.deploy_dir == "/deploy"

    def test_group_defaults_to_none(self):
        server = EcflowServer(hostname="h", user="u", deploy_dir="/d")
        assert server.group is None

    def test_group_can_be_set(self):
        server = EcflowServer(
            hostname="h", user="u", deploy_dir="/d", group="mygroup"
        )
        assert server.group == "mygroup"

    def test_field_names(self):
        names = [f.name for f in fields(EcflowServer)]
        assert names == ["hostname", "user", "deploy_dir", "group"]


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestConstants:

    def test_local_host_contains_localhost(self):
        assert "localhost" in local_host

    def test_host_defaults_has_troika(self):
        assert HOST_DEFAULTS["troika"]["troika_config"] == "%TROIKA_CONFIG%"


# ---------------------------------------------------------------------------
# get_host — host type resolution (parametrized across all types)
# ---------------------------------------------------------------------------


class TestGetHostTypeResolution:
    """Verify correct pyflow host class for every host type."""

    def test_returns_correct_host_class(self, host_config):
        host, _ = _make_host(host_config)
        assert isinstance(host, host_config["expected_class"])

    def test_returns_tuple(self, host_config):
        result = _make_host(host_config)
        assert isinstance(result, tuple) and len(result) == 2


# ---------------------------------------------------------------------------
# get_host — HOST variable (parametrized across all types)
# ---------------------------------------------------------------------------


class TestGetHostVariable:
    """HOST extra variable is always set to %SCHOST:<resolved_hostname>%."""

    def test_host_variable_set(self, host_config):
        host, _ = _make_host(host_config)
        hostname = host_config["hostname"]
        # resolve the actual hostname after type:host parsing
        if ":" in hostname:
            resolved = hostname.split(":")[1]
        else:
            resolved = hostname
        assert host.extra_variables["HOST"] == f"%SCHOST:{resolved}%"


# ---------------------------------------------------------------------------
# get_host — name=%HOST% (parametrized across all types)
# ---------------------------------------------------------------------------


class TestGetHostName:
    """The host name kwarg is always set to %HOST%."""

    def test_host_name_is_percent_host(self, host_config):
        host, _ = _make_host(host_config)
        assert host.name == "%HOST%"


# ---------------------------------------------------------------------------
# get_host — extra_variables (parametrized across all types)
# ---------------------------------------------------------------------------


class TestGetHostExtraVariables:

    def test_user_extra_variables_preserved(self, host_config):
        host, _ = _make_host(host_config, extra_variables={"MY_VAR": "value"})
        assert host.extra_variables["MY_VAR"] == "value"
        assert "HOST" in host.extra_variables

    def test_none_extra_variables_still_sets_host(self, host_config):
        host, _ = _make_host(host_config, extra_variables=None)
        assert "HOST" in host.extra_variables

    def test_empty_extra_variables_still_sets_host(self, host_config):
        host, _ = _make_host(host_config, extra_variables={})
        assert "HOST" in host.extra_variables


# ---------------------------------------------------------------------------
# get_host — submit_arguments (parametrized across all types)
# ---------------------------------------------------------------------------


class TestGetHostSubmitArguments:

    def test_none_returns_empty_variables(self, host_config):
        _, variables = _make_host(host_config, submit_arguments=None)
        assert variables == {}

    def test_empty_returns_empty_variables(self, host_config):
        _, variables = _make_host(host_config, submit_arguments={})
        assert variables == {}

    def test_defaults_extracted_as_uppercase_variables(self, host_config):
        _, variables = _make_host(
            host_config,
            submit_arguments=dict(
                defaults=dict(job_name="%TASK%", account="myproject"),
                serial=dict(queue="nf", total_tasks=1),
                parallel=dict(queue="np"),
            ),
        )
        assert variables["JOB_NAME"] == "%TASK%"
        assert variables["ACCOUNT"] == "myproject"

    def test_contexts_merged_with_defaults(self, host_config):
        host, _ = _make_host(
            host_config,
            submit_arguments=dict(
                defaults=dict(account="proj"),
                serial=dict(queue="nf"),
            ),
        )
        sa = host.submit_arguments
        # serial context should contain both the default and its own key
        assert sa["serial"]["account"] == "proj"
        assert sa["serial"]["queue"] == "nf"


# ---------------------------------------------------------------------------
# get_host — kwargs ingestion (parametrized across all types)
# ---------------------------------------------------------------------------


class TestGetHostKwargsIngestion:

    def test_ecflow_path_forwarded(self, host_config):
        host, _ = _make_host(host_config)
        assert host.ecflow_path == "/usr/bin"

    def test_user_forwarded(self, host_config):
        host, _ = _make_host(host_config)
        assert host.user == "testuser"


# ---------------------------------------------------------------------------
# get_host — HOST_DEFAULTS merging
# ---------------------------------------------------------------------------


class TestGetHostDefaults:

    def test_troika_gets_default_troika_config(self, troika_config):
        host, _ = _make_host(troika_config)
        assert host.troika_config == "%TROIKA_CONFIG%"

    def test_troika_config_overridden_by_kwarg(self, troika_config):
        host, _ = _make_host(troika_config, troika_config="/custom/config")
        assert host.troika_config == "/custom/config"

    def test_non_troika_has_no_troika_defaults(self, localhost_config):
        host, _ = _make_host(localhost_config)
        assert not hasattr(host, "troika_config")


# ---------------------------------------------------------------------------
# get_host — hostname:type parsing edge cases
# ---------------------------------------------------------------------------


class TestGetHostTypeParsing:

    def test_bare_hostname_defaults_to_troika(self):
        """Non-localhost bare hostname → troika."""
        host, _ = get_host(
            hostname="remote-box",
            user="u",
            ecflow_path="/usr/bin",
        )
        assert isinstance(host, pf.TroikaHost)

    def test_bare_localhost_detected(self):
        host, _ = get_host(
            hostname="localhost",
            user="u",
            ecflow_path="/usr/bin",
        )
        assert isinstance(host, pf.LocalHost)

    @pytest.mark.parametrize(
        "hostname, expected_resolved",
        [
            ("troika:myhost", "myhost"),
            ("slurm:myhost", "myhost"),
            ("pbs:myhost", "myhost"),
            ("ssh:myhost", "myhost"),
            ("localhost:myhost", "myhost"),
        ],
    )
    def test_colon_syntax_resolves_hostname(self, hostname, expected_resolved):
        host, _ = get_host(
            hostname=hostname,
            user="u",
            ecflow_path="/usr/bin",
        )
        assert host.extra_variables["HOST"] == f"%SCHOST:{expected_resolved}%"


# ---------------------------------------------------------------------------
# Integration with conftest slurmhost_config fixture
# ---------------------------------------------------------------------------


class TestGetHostIntegration:

    def test_slurmhost_config_fixture(self, slurmhost_config):
        host, variables = get_host(**slurmhost_config["host"])
        assert variables["JOB_NAME"] == "%TASK%"
        assert variables["ACCOUNT"] == "project"

    def test_wlhost_fixture(self, wlhost):
        assert wlhost.host is not None
        assert isinstance(wlhost.defaults, dict)
