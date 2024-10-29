import os
import shutil

import pyflow as pf

local_host = ["localhost"]


def get_host(
    hostname: str,
    user: str,
    ecflow_path: str = None,
    server_ecfvars: bool = False,
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
        print("Running on host: " + str(hostname))
    else:
        host = pf.TroikaHost(
            "%HOST%",
            user=user,
            extra_variables={"HOST": f"%SCHOST:{hostname}%"},
            server_ecfvars=server_ecfvars,
            ecflow_path=ecflow_path,
            **kwargs,
        )
        print("Submitting jobs using troika on host: " + str(hostname))

    return host
