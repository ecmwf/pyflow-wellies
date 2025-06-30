import os
import shutil
from dataclasses import dataclass

import pyflow as pf

from wellies.config import parse_submit_arguments

local_host = ["localhost"]


@dataclass
class EcflowServer:
    """Class to store ecflow server configuration"""

    hostname: str
    user: str
    deploy_dir: str
    group: str = None  # Optional suites group for the ecflow server


def get_host(
    hostname: str,
    user: str,
    ecflow_path: str = None,
    server_ecfvars: bool = False,
    extra_variables: dict = None,
    submit_arguments: dict = None,
    **kwargs,
) -> pf.Host:
    """
    Returns a pyflow host object based on the given hostname and user.

    Parameters
    ----------
    hostname (str):
        The name of the host to connect to.
    user (str):
        The username to use when connecting to the host.
    ecflow_path (str, optional):
        The path to the ecflow_client executable.
        If None, try to get the current path from the ecflow_client
        executable.
        Defaults to None.
    server_ecfvars (bool, optional):
        Whether to use server-side ECF_ variables. Defaults to False.
    extra_variables (dict, optional):
        Additional ecflow variables to set on the host
    **kwargs:
        Additional keyword arguments to pass to the pyflow host
        constructor.

    Returns:
        Union[pf.LocalHost, pf.TroikaHost]: A pyflow host object.
    """
    if ecflow_path is None:
        ecflow_path = os.path.dirname(shutil.which("ecflow_client"))

    options = submit_arguments or {}
    submit_arguments, variables = parse_submit_arguments(options)
    if hostname in local_host:
        host = pf.LocalHost(
            hostname,
            user=user,
            ecflow_path=ecflow_path,
            submit_arguments=submit_arguments,
            **kwargs,
        )
        print("Running on host: " + str(hostname))
    else:
        extra_variables = extra_variables or {}
        extra_variables["HOST"] = f"%SCHOST:{hostname}%"
        host = pf.TroikaHost(
            "%HOST%",
            user=user,
            extra_variables=extra_variables,
            server_ecfvars=server_ecfvars,
            ecflow_path=ecflow_path,
            submit_arguments=submit_arguments,
            **kwargs,
        )
        print("Submitting jobs using troika on host: " + str(hostname))

    return host, variables
