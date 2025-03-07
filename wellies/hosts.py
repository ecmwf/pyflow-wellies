import os
import shutil

import pyflow as pf

local_host = ["localhost"]


def get_host(
    hostname: str,
    user: str,
    ecflow_path: str = None,
    server_ecfvars: bool = False,
    extra_variables: dict = None,
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

    if hostname in local_host:
        host = pf.LocalHost(
            hostname, user=user, ecflow_path=ecflow_path, **kwargs
        )
        print("running on host: " + str(hostname))
    else:
        extra_variables = {"HOST": f"%SCHOST:{hostname}%", **(extra_variables or {})},

        host = pf.TroikaHost(
            "%HOST%",
            user=user,
            extra_variables=extra_variables,
            server_ecfvars=server_ecfvars,
            ecflow_path=ecflow_path,
            **kwargs,
        )
        print("submitting jobs using troika on host: " + str(hostname))

    return host
