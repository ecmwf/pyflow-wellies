import os
from os import path
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import pyflow as pf

from wellies import data
from wellies import scripts

module_use = """
module use {{ MODULEFILES }}
"""

module_load = """
set +ux
module unload {{ NAME }} || true
module load {{ NAME }}/{{ VERSION }}
set -ux
"""
module_unload = """
module unload {{ NAME }}
"""

env_path_load = """
export {{ NAME }}={{ VALUE }}:${{ '{'}}{{ NAME }}:-}
"""
env_path_unload = """
echo 'removing {{ VALUE }} from ${{ NAME }}'
export {{ NAME }}=${{ '{'}}{{ NAME }}/{{ VALUE }}:/}
echo '$PATH after removing' && echo ${{ NAME }}
"""

env_var_load = """
export {{ NAME }}={{ VALUE }}
"""

env_var_unload = """
unset ${{ NAME }}
"""

conda_load = """
set +ux
{{ CONDA_ACTIVATE_CMD }} activate {{ TARGET }}
set -ux
"""

conda_setup_yaml = """
rm -rf {{ ENV_DIR }}
{{ CONDA_CMD }} env create --file {{ ENV_FILE }} -p {{ ENV_DIR }}
"""

conda_setup_file = """
rm -rf {{ ENV_DIR }}
{{ CONDA_CMD }} create --file {{ ENV_FILE }} -p {{ ENV_DIR }}
"""

conda_create = """
rm -rf {{ ENV_DIR }}
{{ CONDA_CMD }} create -p {{ ENV_DIR }} {{ PACKAGES }}
"""


def deploy_package_script(
    package: str,
    options: Dict[str, any],
    lib_dir: str = "$LIB_DIR",
    build_dir: str = None,
):
    """
    Creates a script that deploys a package on the target machine.
    The package is installed in the lib_dir/build directory.

    Parameters
    ----------
    package: str
        name of the package
    options: dict
        dictionary of options for the package
    lib_dir: str
        directory where to install the package  (default: $LIB_DIR)
    """
    build_dir = build_dir or os.path.join(lib_dir, "build", "${ENV_NAME:-" "}")
    data_installer = data.parse_data_item(build_dir, package, options)

    script = [
        data_installer.script,
        scripts.update_label_version(),
    ]

    return script


class Tool:
    def __init__(
        self,
        name: str,
        depends: Union[List[str], str] = [],
        load: Union[List[str], str] = "",
        unload: Union[List[str], str] = "",
        setup: Union[List[str], str] = "",
        options: Dict[str, any] = {},
    ):
        """
        A tool is a software that can be loaded/unloaded in the task script.
        The tool can be a module, a package, a virtual environment, etc.
        A tool provides three scripts:
        - load: script to load the tool
        - unload: script to unload the tool
        - setup: script to install the tool (in the deploy family)

        Parameters
        ----------
        name: str
            name of the tool
        depends: list of str
            list of tools that must be loaded before this tool
        load: str or list of str
            bash script to load the tool
        unload: str or list of str
            bash script to unload the tool
        setup: str or list of str
            bash script to setup the tool
        options: dict
            dictionary of options for the tool
        """
        self.name = name
        self.options = options
        self.depends = depends if isinstance(depends, list) else [depends]
        self.scripts = {}
        self.scripts["load"] = load
        self.scripts["unload"] = unload
        self.scripts["setup"] = setup


class ModuleTool(Tool):
    def __init__(
        self,
        name: str,
        module_name: str,
        version: str,
        depends: List[str] = [],
        options: Dict[str, any] = {},
    ):
        """
        A module tool is a tool that can be loaded/unloaded using the
        module system.

        Parameters
        ----------
        name: str
            name of the tool
        module_name: str
            name of the module
        version: str
            version of the module
        depends: list of str
            list of tools that must be loaded before this tool
        options: dict
            dictionary of options for the tool
        """
        load = pf.TemplateScript(
            module_load, NAME=module_name, VERSION=version
        )
        unload = pf.TemplateScript(module_unload, NAME=module_name)
        super().__init__(name, depends, load, unload, options=options)


class PrivateModuleTool(Tool):
    def __init__(
        self,
        name: str,
        module_name: str,
        version: str,
        modulefiles: str,
        depends: List[str] = [],
        options: Dict[str, any] = {},
    ):
        """
        Extension of the ModuleTool class to load a module from a custom
        modulefile path.

        Parameters
        ----------
        name: str
            name of the tool
        module_name: str
            name of the module
        version: str
            version of the module
        modulefiles: str
            path to the custom modulefile
        depends: list of str
            list of tools that must be loaded before this tool
        options: dict
            dictionary of options for the tool
        """
        load = pf.TemplateScript(
            module_use + module_load,
            NAME=module_name,
            VERSION=version,
            MODULEFILES=modulefiles,
        )
        unload = pf.TemplateScript(module_unload, NAME=module_name)
        super().__init__(name, depends, load, unload, options=options)


class EnvVarTool(Tool):
    def __init__(
        self,
        name: str,
        var: str,
        value: str,
        setup: Union[List[str], str] = None,
        depends: List[str] = [],
        options: Dict[str, any] = {},
    ):
        """
        Environment variable tool.
        When loading, it set the environment variable to the given value.
        If the value contains the string PATH (for instance PATH or
        PYTHONPATH), then the value is added to the environment variable.
        For instance:
        export PATH=/this/his/the/path:$PATH

        Parameters
        ----------
        name: str
            name of the tool
        var: str
            name of the envirpnment variable
        value: str
            path to set to the environment variable
        setup: str or list of str
            setup script used to deploy the tool
        depends: list of str
            list of tools that must be loaded before this tool
        options: dict
            dictionary of options for the tool
        """
        load_tplt = env_var_load
        unload_tplt = env_var_unload
        if "PATH" in var.upper():
            load_tplt = env_path_load
            unload_tplt = env_path_unload

        load = pf.TemplateScript(load_tplt, NAME=var, VALUE=value)
        unload = pf.TemplateScript(unload_tplt, NAME=var, VALUE=value)
        super().__init__(
            name, depends, load, unload, setup=setup, options=options
        )


class FolderTool(EnvVarTool):
    def __init__(
        self,
        name: str,
        lib_dir: str,
        depends: List[str] = [],
        options: Dict[str, any] = {},
    ):
        """
        Folder tool extending the environment variable tool.
        It updates the PATH environment variable to include the folder located
        in lib_dir/name.

        Parameters
        ----------
        name: str
            name of the tool.
        lib_dir: str
            path to the lib directory of the suite.
        depends: list of str
            list of tools that must be loaded before this tool.
        options: dict
            dictionary of options for the tool.
        """
        folder_path = path.join(lib_dir, name)
        setup = [
            f"rm -rf {folder_path}",
            f"mkdir -p {folder_path}",
        ]
        super().__init__(
            name, "PATH", folder_path, setup, depends, options=options
        )


class PackageTool(Tool):
    def __init__(self, name: str, lib_dir: str, options: Dict[str, any]):
        """
        Package tool that installs a user package in an environment.
        The package is downloaded in the lib_dir/build directory and the user
        must provide a script to install the package in the environment.

        Parameters
        ----------
        name: str
            name of the tool.
        lib_dir: str
            path to the lib directory.
        options: dict
            dictionary of options for the tool.
        """
        depends = options.get("depends", [])
        build_dir = options.get("build_dir")
        setup = deploy_package_script(name, options, lib_dir, build_dir)
        super().__init__(name, depends, setup=setup, options=options)


class VirtualEnvTool(Tool):
    def __init__(
        self,
        name: str,
        lib_dir: str,
        venv_options: Union[str, List[str]] = "",
        extra_packages: Union[str, List[str]] = [],
        depends: List[str] = [],
        options: Dict[str, any] = {},
    ):
        """
        A tool that creates a python virtual environment and sets the right
        scripts to load it, unload it and install it.

        Parameters
        ----------
        name : str
            The name of the tool.
        lib_dir : str
            The path to the lib directory.
        venv_options : Union[str, List[str]], optional
            Additional options to pass to the `python3 -m venv` command, by
            default "".
        depends : List[str], optional
            A list of dependencies for the tool, by default [].
        options : Dict[str], optional
            A dictionary of options for the tool, by default {}.
        """
        env_root = path.join(lib_dir, name)
        load = [
            "\nsource {}".format(path.join(env_root, "bin", "activate")),
            "export LD_LIBRARY_PATH={}:${{LD_LIBRARY_PATH:=}}".format(
                path.join(env_root, "lib")
            ),
        ]
        unload = "deactivate"
        if not isinstance(venv_options, list):
            venv_options = [venv_options]
        opts = " ".join(venv_options)
        setup = [
            f"rm -rf {env_root}",
            f"python3 -m venv {env_root} {opts}",
        ]
        if extra_packages:
            setup.extend(load)
            pkgs = " ".join(extra_packages)
            setup.append(f"pip install {pkgs}")
        super().__init__(name, depends, load, unload, setup, options=options)


class SystemEnvTool(VirtualEnvTool):
    def __init__(
        self,
        name: str,
        lib_dir: str,
        venv_options: Union[str, List[str]] = "",
        extra_packages: Union[str, List[str]] = [],
        depends: List[str] = [],
        options: Dict[str, any] = {},
    ):
        """
        An extension of the VirtualEnvTool class that creates a python virtual
        environment that extends the current environment, i.e. with the
        --system-site-packages option.

        Parameters
        ----------
        name : str
            The name of the tool.
        lib_dir : str
            The path to the lib directory.
        venv_options : Union[str, List[str]], optional
            Additional options to pass to the `python3 -m venv` command, by
            default "".
        depends : List[str], optional
            A list of dependencies for the tool, by default [].
        options : Dict[str], optional
            A dictionary of options for the tool, by default {}.
        """
        to_add = [" --system-site-packages"]
        if venv_options:
            if isinstance(venv_options, str):
                venv_options = [venv_options]
            to_add.extend(venv_options)

        super().__init__(
            name,
            lib_dir,
            venv_options=to_add,
            extra_packages=extra_packages,
            depends=depends,
            options=options,
        )


class CondaEnvTool(Tool):
    def __init__(
        self,
        name: str,
        environment: str,
        setup: str = None,
        depends: List[str] = [],
        conda_activate_cmd: str = "conda",
        options: Dict[str, str] = {},
    ):
        """
        An environment tool that can load and unload a conda environment.

        Parameters
        ----------
        name : str
            The name of the tool.
        environment : str
            The name or path of the conda environment.
        setup : str, optional
            The setup script, by default None.
        depends : List[str], optional
            A list of dependencies for the tool, by default [].
        conda_activate_cmd : str, optional
            The conda command to use to load the environment,
            some login-nodes require "source" instead of "conda"
            by default "conda".
        options : Dict[str, str], optional
            A dictionary of options for the tool, by default {}.
        """
        load = pf.TemplateScript(
            conda_load,
            TARGET=environment,
            CONDA_ACTIVATE_CMD=conda_activate_cmd,
        )
        unload = f"{conda_activate_cmd} deactivate"
        super().__init__(name, depends, load, unload, setup, options=options)


class FileCondaEnvTool(CondaEnvTool):
    def __init__(
        self,
        name: str,
        lib_dir: str,
        env_file: str,
        depends: List[str] = [],
        conda_cmd: str = "conda",
        conda_activate_cmd: str = "conda",
        options: Dict[str, any] = {},
    ):
        """
        An extension of the CondaEnvTool class that also creates a conda
        environment in the lib directory.
        The conda environment is created from a conda environment file.
        The path to the environment file is specified as a dictionary following
        the StaticData options format, for instance:
        ```yaml
        my_env:
            env_file:
                type: copy
                source: /path/to/environment.yml
        my_env2:
            env_file:
                type: git
                source: git@github.com:myrepo.git
                branch: master
                files: myenvironment.yml
        ```

        Parameters
        ----------
        name : str
            The name of the tool.
        lib_dir : str
            The path to the lib directory of the suite.
        env_file : str
            The options to retrieve the environment file.
        depends : List[str], optional
            A list of dependencies for the tool, by default [].
        conda_cmd : str, optional
            The conda command to use, by default "conda".
        options : Dict[str, str], optional
            A dictionary of options for the tool, by default {}.
        """
        env_root = path.join(lib_dir, name)
        build_dir = options.get("build_dir", path.join(lib_dir, "build"))
        fname = env_file.get("files", os.path.basename(env_file["source"]))
        file_setup = data.parse_data_item(build_dir, name, env_file)

        env_file_path = path.join(build_dir, name, fname)

        setup = pf.TemplateScript(
            conda_setup_yaml,
            ENV_FILE=env_file_path,
            ENV_DIR=env_root,
            CONDA_CMD=conda_cmd,
        )
        setup_script = [file_setup.script, setup]
        super().__init__(
            name,
            env_root,
            setup_script,
            depends,
            conda_activate_cmd,
            options=options,
        )


class SimpleCondaEnvTool(CondaEnvTool):
    def __init__(
        self,
        name: str,
        lib_dir: str,
        packages: Union[str, List[str]],
        depends: List[str] = [],
        conda_cmd: str = "conda",
        conda_activate_cmd: str = "conda",
        options: Dict[str, any] = {},
    ):
        """
        An extension of the CondaEnvTool class that also creates a conda
        environment in the lib directory.
        The conda environment is created from a list of conda packages.

        Parameters
        ----------
        name : str
            The name of the tool.
        lib_dir : str
            The path to the lib directory of the suite.
        packages : str or list of str
            The options to retrieve the environment file.
        depends : List[str], optional
            A list of dependencies for the tool, by default [].
        conda_cmd : str, optional
            The conda command to use, by default "conda".
        options : Dict[str, str], optional
            A dictionary of options for the tool, by default {}.
        """
        env_root = path.join(lib_dir, name)
        packages_str = " ".join(packages)
        setup = pf.TemplateScript(
            conda_create,
            ENV_DIR=env_root,
            PACKAGES=packages_str,
            CONDA_CMD=conda_cmd,
        )
        super().__init__(
            name, env_root, setup, depends, conda_activate_cmd, options=options
        )


def parse_environment(
    lib_dir: str, name: str, options: Dict[str, any]
) -> Tool:
    """
    Create an environment tool based on the given options.

    Parameters
    ----------
    lib_dir : str
        The lib directory of the suite where the tools are installed.
    name : str
        The name of the environment.
    options : dict
        A dictionary containing the environment options.

    Returns
    -------
    Tool: A Tool object representing the environment.

    Raises
    -------
    Exception: If the environment type is not supported or if certain
        options are used together.
    NotImplementedError: If the environment type is not implemented.
    """
    type = options["type"]
    depends = options.get("depends", [])
    if type == "folder":
        env = FolderTool(name, lib_dir, depends=depends)
    elif type == "system_venv":
        extra_packages = options.get("extra_packages", [])
        venv_options = options.get("venv_options", [])
        env = SystemEnvTool(
            name,
            lib_dir,
            venv_options=venv_options,
            extra_packages=extra_packages,
            depends=depends,
        )
    elif type == "conda" and "environment" in options:
        if "env_file" in options or "extra_packages" in options:
            raise Exception(
                "environment, file and extra_packages options cannot be used at the same time for conda"  # noqa: E501
            )
        environment = options["environment"]
        env = CondaEnvTool(
            name,
            environment,
            depends=depends,
            conda_activate_cmd=options.get("conda_activate_cmd", "conda"),
        )
    elif type == "conda" and "env_file" in options:
        if "environment" in options:
            raise Exception(
                "environment and file options cannot be used at the same time for conda"  # noqa: E501
            )
        env = FileCondaEnvTool(
            name,
            lib_dir,
            options["env_file"],
            depends,
            conda_cmd=options.get("conda_cmd", "conda"),
            conda_activate_cmd=options.get("conda_activate_cmd", "conda"),
        )
    elif type == "conda" and "extra_packages" in options:
        if "environment" in options:
            raise Exception(
                "environment and extra_packages options cannot be used at the same time for conda"  # noqa: E501
            )
        conda_packages = options["extra_packages"]
        env = SimpleCondaEnvTool(
            name,
            lib_dir,
            conda_packages,
            depends,
            conda_cmd=options.get("conda_cmd", "conda"),
            conda_activate_cmd=options.get("conda_activate_cmd", "conda"),
        )
    elif type == "custom":
        env = Tool(
            name,
            depends,
            options.get("load", ""),
            options.get("unload", ""),
            options.get("setup", None),
        )
    elif type == "venv":
        venv_options = options.get("venv_options", "")
        extra_packages = options.get("extra_packages", [])
        env = VirtualEnvTool(
            name,
            lib_dir,
            venv_options=venv_options,
            extra_packages=extra_packages,
            depends=depends,
            options=options,
        )
    else:
        raise Exception("Environment type {} not supported".format(type))
    return env


def parse_package(
    lib_dir: str, name: str, options: Dict[str, any]
) -> PackageTool:
    """
    Create a package tool based on the given options.

    Parameters
    ----------
    lib_dir : str
        The lib directory of the suite where the tools are installed.
    name : str
        The name of the package.
    options : dict
        A dictionary containing the package options.

    Returns
    -------
    PackageTool: A Tool object representing the package.
    """
    package = PackageTool(name, lib_dir, options)
    return package


def parse_module(name: str, options: Dict[str, any]) -> Tool:
    """
    Create a module tool based on the given options.

    Parameters
    ----------
    name : str
        The name of the module.
    options : dict
        A dictionary containing the module options.

    Returns
    -------
    Tool: Either a ModuleTool or a PrivateModuleTool object.
    """
    module_name = options.get("name", name)
    version = options.get("version", "default")
    depends = options.get("depends", [])
    modulefiles = options.get("modulefiles", "")
    if modulefiles:
        module = PrivateModuleTool(
            name, module_name, version, modulefiles, depends
        )
    else:
        module = ModuleTool(name, module_name, version, depends)
    return module


def parse_env_var(name: str, options: Dict[str, any]) -> EnvVarTool:
    """
    Create an environment variable tool based on the given options.

    Parameters
    ----------
    name : str
        The name of the environment.
    options : dict
        A dictionary containing the environment options.

    Returns
    -------
    Tool: A Tool object representing the environment variable tool.
    """
    variable = options.get("variable", name)
    value = options.get("value", "")
    depends = options.get("depends", [])
    var = EnvVarTool(name, variable, value, depends=depends)
    return var


class ToolStore:
    def __init__(self, lib_dir: str, options: Dict[str, any]):
        """
        The ToolStore class is a container for all the tools of a suite.
        The constructor parses the options and creates the tools.

        Parameters
        ----------
        lib_dir : str
            The path to the lib directory of the suite.
        options : Dict[str, str], optional
            A dictionary of options containing all the tools and their options.
        """
        if options is None:
            options = {}
        self.modules = options.get("modules", {})
        self.packages = options.get("packages", {})
        self.environments = options.get("environments", {})
        self.env_vars = options.get("env_variables", {})
        self.dir = lib_dir

        # Build tools
        self.tools = {}

        # modules:
        for name, options in self.modules.items():
            module = parse_module(name, options)
            self.add_tool(name, module)

        # packages
        for name, options in self.packages.items():
            package = parse_package(lib_dir, name, options)
            self.add_tool(name, package)

        # environments
        for name, options in self.environments.items():
            env = parse_environment(lib_dir, name, options)
            self.add_tool(name, env)

        # environment variables
        for name, options in self.env_vars.items():
            var = parse_env_var(name, options)
            self.add_tool(name, var)

    def add_tool(self, toolname: str, tool: Tool):
        """
        Adds a tool to the tool store.

        Parameters
        ----------
        toolname : str
            The name of the tool.
        tool : Tool
            The tool object to add to the dictionary of tools.
        """
        self.tools[toolname] = tool

    def tool_script(self, script_type: str, toolname: str) -> dict:
        """
        Returns the script of a tool and its dependencies.

        Parameters
        ----------
        script_type : str
            The type of script (load, unload or setup).
        toolname : str
            The name of the tool.

        Returns
        -------
        dict: a dictionary of tools -> scripts
        """
        tool = self.tools[toolname]
        script = {}
        for item in tool.depends:
            script.update(self.tool_script(script_type, item))
        if tool.scripts[script_type]:
            script[toolname] = tool.scripts[script_type]
        return script

    def load(self, tools: Union[List[str], str]) -> list:
        """
        Returns the load script of one or multiple tools.

        Parameters
        ----------
        tools : str or list of str
            The tools to load.

        Returns
        -------
        list : a list of scripts to load the tools
        """
        if not isinstance(tools, list):
            tools = [tools]
        script = {}
        script["head"] = "# load tools and activate environment"
        for item in tools:
            script.update(self.tool_script("load", item))
        return list(script.values())

    def unload(self, tools: Union[List[str], str]):
        """
        Returns the unload script of one or multiple tools.
        In this case we reverse the dependency order to unload the tools.

        Parameters
        ----------
        tools : str or list of str
            The tools to unload.

        Returns
        -------
        list : a list of scripts to unload the tools
        """
        if not isinstance(tools, list):
            tools = [tools]
        script = {}
        script["head"] = "# unload tools and deactivate environment"
        for item in tools:
            # reverse dictionary to unload
            unload_script = self.tool_script("unload", item)
            unload_script = unload_script.fromkeys(
                reversed(list(unload_script.keys()))
            )
            script.update(unload_script)
        return list(script.values())

    def setup(self, toolname: str) -> list:
        """
        Returns the setup script of the tool.

        Parameters
        ----------
        toolname : str
            The tool to setup.

        Returns
        -------
        list : a list of scripts to setup the tool
        """
        script = {}
        script["head"] = "# load tools and activate environment"
        tool = self.tools[toolname]
        for item in tool.depends:
            script.update(self.tool_script("load", item))
        script[toolname] = tool.scripts["setup"]
        return list(script.values())

    def depends(self, toolname: str) -> list:
        """
        Returns the dependencies of a tool.

        Parameters
        ----------
        toolname : str
            The name of the tool.

        Returns
        -------
        list : the list of dependcies of the tool
        """
        tool = self.tools[toolname]
        depends = []
        for item in tool.depends:
            depends += [item]
            depends += self.depends(item)
        return depends

    def __getitem__(self, item):
        return self.tools[item]

    def items(self):
        return self.tools.items()


class DeployPackagesFamily(pf.Family):
    """
    A deployment family class for the packages of an environment.
    """

    def __init__(
        self,
        tools: ToolStore,
        env_packages: List[str],
        env: str,
        submit_arguments: Dict[str, str],
        **kwargs,
    ):
        super().__init__(name="packages", **kwargs)

        with self:
            deploy_tasks = {}
            for package in env_packages:
                package_tool = tools[package]
                tool_script = [
                    tools.load(env),
                    tools.setup(package),
                ]
                deploy_tasks[package] = pf.Task(
                    name=package,
                    submit_arguments=package_tool.options.get(
                        "submit_arguments", submit_arguments
                    ),
                    script=tool_script,
                    labels={"version": "NA"},
                )
        # create dependencies between packages tasks
        for package in env_packages:
            for depend in tools[package].depends:
                if depend in env_packages:
                    deploy_tasks[package].triggers = (
                        deploy_tasks[package].triggers
                        & deploy_tasks[depend].complete
                    )


class DeployToolsFamily(pf.AnchorFamily):
    """
    The deployTools Family contains all the nodes required to install the tools
    of the suite in the target location (lib directory, $LIB_DIR).

    The structure is the following:
        - The first level contains the environments, which includes a setup
        Task.
        - The second level contains the packages to install in the environment.

    The environment will be created in $LIB_DIR/env_name.
    """

    def __init__(
        self,
        tools: ToolStore,
        submit_arguments: Optional[Dict[str, str]] = None,
        name: str = "deploy_tools",
        **kwargs,
    ):
        """
        Creates the DeployToolsFamily and pass the extra arguments to the
        Family constructor.

        Parameters
        ----------
        tools : ToolStore
            The name of the tool.
        submit_arguments : Dict[str, any], optional
            The execution context of the nodes, by default {}.
        """
        super().__init__(name=name, **kwargs)

        if submit_arguments is None:
            submit_arguments = {}

        with self:
            has_tasks = False
            env_families = {}
            for env, options in tools.environments.items():
                env_tool = tools[env]
                if env_tool.scripts["setup"] is not None:
                    has_tasks = True
                    with pf.AnchorFamily(
                        name=env, variables={"ENV_NAME": env}
                    ) as env_families[env]:
                        env_task = pf.Task(
                            name="setup",
                            submit_arguments=env_tool.options.get(
                                "submit_arguments", submit_arguments
                            ),
                            script=tools.setup(env),
                        )
                        if "packages" in options:
                            env_packages = options["packages"]
                            package_family = DeployPackagesFamily(
                                tools, env_packages, env, submit_arguments
                            )
                            package_family.triggers = env_task.complete

            # create dependencies between environments tasks
            for env in tools.environments:
                for depend in tools[env].depends:
                    if depend in env_families:
                        env_families[env].triggers = (
                            env_families[env].triggers
                            & env_families[depend].complete
                        )

            if not has_tasks:
                self.defstatus = pf.state.complete
