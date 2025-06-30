# flake8: noqa
import os
from functools import partial
from textwrap import dedent

import pyflow as pf
import pytest

import wellies as wl
from wellies import tools


def test_tool_store(custom_script_file):
    lib_dir = os.path.join("path", "to", "lib")
    tools_dict = {
        "modules": {
            "python3": {"version": 3.8},
            "private": {
                "version": "2023.04.1.0",
                "modulefiles": "/path/to/private/module",
                "depends": "python3",
            },
        },
        "packages": {
            "mypackage1": {
                "type": "git",
                "source": "git.example.com/repo.git",
                "branch": "develop",
                "post_script": "some installer",  # to silence warning
            },
            "mypackage2": {
                "type": "rsync",
                "source": os.path.join("dir", "to", "package"),
                "post_script": f"{custom_script_file}",
            },
        },
        "environments": {
            "myenv1": {"type": "conda", "environment": "mycondaenv"},
            "myenv2": {
                "type": "system_venv",
                "packages": ["mypackage1", "mypackage2"],
                "depends": "python3",
            },
        },
        "env_variables": {
            "bin": {
                "variable": "PATH",
                "value": "/path/to/local/bin",
                "depends": ["private"],
            },
        },
    }

    toolstore = tools.ToolStore(lib_dir, tools_dict)

    ref_class = {
        "python3": tools.ModuleTool,
        "private": tools.PrivateModuleTool,
        "mypackage1": tools.PackageTool,
        "mypackage2": tools.PackageTool,
        "myenv1": tools.CondaEnvTool,
        "myenv2": tools.SystemEnvTool,
        "bin": tools.EnvVarTool,
    }

    for name, data in toolstore.items():
        assert isinstance(data, ref_class[name])

    assert toolstore.depends("bin") == ["private", "python3"]
    assert toolstore.depends("myenv2") == ["python3"]


class BaseToolScriptsTest:
    lib_dir = "/path/to/lib"

    def _get_tool_parser(self):
        opts = {
            "environments": partial(
                wl.tools.parse_environment, lib_dir=self.lib_dir
            ),
            "packages": partial(wl.tools.parse_package, lib_dir=self.lib_dir),
            "modules": wl.tools.parse_module,
        }
        return opts[self.section]

    def _run(self, test_target, expected, tools_config):
        name = test_target
        options = tools_config[self.section][test_target]
        tool = self._get_tool_parser()(name=name, options=options)

        for name in expected.keys():
            entry_script = tool.scripts[name]
            if not entry_script:
                assert not expected[name]
                continue
            elif isinstance(entry_script, pf.Script):
                entry_script = entry_script.generate_stub()
            elif isinstance(entry_script, list):
                entry_script = pf.Script.generate_list_scripts(entry_script)
            print(entry_script)
            for entry in expected[name]:
                if entry:
                    assert entry in entry_script


class TestEnvToolsScripts(BaseToolScriptsTest):
    section = "environments"

    def test_folder_env(self, tools_config):
        test_target = "bin"

        expected = {
            "load": [
                f"export PATH={self.lib_dir}/{test_target}" + ":${PATH:-}"
            ],
            "unload": [
                f"echo 'removing {self.lib_dir}/{test_target} from $PATH'",
                "export PATH=${PATH/"
                + f"{self.lib_dir}/{test_target}"
                + ":/}",
                "echo '$PATH after removing' && echo $PATH",
            ],
            "setup": [
                f"rm -rf {self.lib_dir}/{test_target}",
                f"mkdir -p {self.lib_dir}/{test_target}",
            ],
        }

        self._run(test_target, expected, tools_config)

    def test_system_venv(self, tools_config):
        test_target = "myenv1"
        extra_pkgs = tools_config["environments"][test_target][
            "extra_packages"
        ]
        extra_pkgs = " ".join(extra_pkgs)

        expected = {
            "load": [f"source {self.lib_dir}/{test_target}/bin/activate"],
            "unload": ["deactivate"],
            "setup": [
                f"rm -rf {self.lib_dir}/{test_target}",
                f"python3 -m venv {self.lib_dir}/{test_target}  --system-site-packages",
                f"pip install {extra_pkgs}",
            ],
        }

        self._run(test_target, expected, tools_config)

    def test_pure_venv(self, tools_config):
        test_target = "anemoi_venv"
        expected = {
            "load": [f"source {self.lib_dir}/{test_target}/bin/activate"],
            "unload": ["deactivate"],
            "setup": [
                f"rm -rf {self.lib_dir}/{test_target}",
                f"python3 -m venv {self.lib_dir}/{test_target}",
            ],
        }

        self._run(test_target, expected, tools_config)

    @pytest.mark.xfail(reason="pure venv not implemented")
    def test_rsync_venv(self, tools_config):
        test_target = "venv"
        src_dst = tools_config["environments"][test_target]["env_file"][
            "source"
        ]
        env_file_name = tools_config["environments"][test_target]["env_file"][
            "files"
        ]
        opts = tools_config["environments"][test_target]["env_file"][
            "rsync_options"
        ]

        expected = {
            "load": [f"source {self.lib_dir}/{test_target}/bin/activate"],
            "unload": ["deactivate"],
            "setup": [
                f"mkdir -p {self.lib_dir}/build",
                f"dest_dir={self.lib_dir}/build/{test_target}",
                "rm -rf $dest_dir",
                "mkdir -p $dest_dir",
                f"rsync {opts} {src_dst}/{env_file_name}  $dest_dir/",
                f"rm -rf {self.lib_dir}/{test_target}",
                f"python3 -m venv {self.lib_dir}/{test_target}",
                f"pip install -r {env_file_name}",
            ],
        }

        self._run(test_target, expected, tools_config)

    def test_copy_yaml(self, tools_config):
        test_target = "conda_copy"
        src_dst = tools_config["environments"][test_target]["env_file"][
            "source"
        ]
        env_file_name = tools_config["environments"][test_target]["env_file"][
            "files"
        ]

        expected = {
            "load": [
                "set +ux",
                f"conda activate {self.lib_dir}/{test_target}",
                "set -ux",
            ],
            "unload": ["conda deactivate"],
            "setup": [
                f"mkdir -p {self.lib_dir}/build",
                f"dest_dir={self.lib_dir}/build/{test_target}",
                "rm -rf $dest_dir",
                "mkdir -p $dest_dir",
                "cd $dest_dir",
                f"scp {src_dst}/{env_file_name}  $dest_dir/",
                f"rm -rf {self.lib_dir}/{test_target}",
                f"conda env create --file {self.lib_dir}/build/{test_target}/{env_file_name} -p {self.lib_dir}/{test_target}",
            ],
        }

        self._run(test_target, expected, tools_config)

    def test_conda_exist(self, tools_config):
        test_target = "conda_exist"
        conda_prefix = tools_config["environments"][test_target]["environment"]

        expected = {
            "load": ["set +ux", f"conda activate {conda_prefix}", "set -ux"],
            "unload": ["conda deactivate"],
            "setup": [],
        }

        self._run(test_target, expected, tools_config)

    def test_conda_git_yaml(self, tools_config):
        test_target = "conda_remote_file"
        gitsrc = tools_config["environments"][test_target]["env_file"][
            "source"
        ]
        env_file_name = tools_config["environments"][test_target]["env_file"][
            "files"
        ]
        print(env_file_name)

        expected = {
            "load": [
                "set +ux",
                f"conda activate {self.lib_dir}/{test_target}",
                "set -ux",
            ],
            "unload": ["conda deactivate"],
            "setup": [
                f"mkdir -p {self.lib_dir}/build",
                f"dest_dir={self.lib_dir}/build/git/{test_target}",
                "rm -rf $dest_dir",
                f"giturl={gitsrc}",
                "gitbranch=master",
                "git clone $giturl --branch $gitbranch --single-branch --depth 1 $dest_dir",
                "cd $dest_dir",
                f"dest_dir={self.lib_dir}/build/{test_target}",
                f"rsync -avzpL {self.lib_dir}/build/git/{test_target}/{env_file_name}  $dest_dir/",
                "cd $dest_dir",
                f"rm -rf {self.lib_dir}/{test_target}",
                f"conda env create --file {self.lib_dir}/build/{test_target}/{env_file_name} -p {self.lib_dir}/{test_target}",
            ],
        }

        self._run(test_target, expected, tools_config)

    def test_conda_pkgs(self, tools_config):
        test_target = "conda_pkgs"
        extra_pkgs = tools_config["environments"][test_target][
            "extra_packages"
        ]
        extra_pkgs = " ".join(extra_pkgs)
        conda_cmd = tools_config["environments"][test_target]["conda_cmd"]

        expected = {
            "load": [
                "set +ux",
                f"conda activate {self.lib_dir}/{test_target}",
                "set -ux",
            ],
            "unload": ["conda deactivate"],
            "setup": [
                f"rm -rf {self.lib_dir}/{test_target}",
                f"{conda_cmd} create -p {self.lib_dir}/{test_target} {extra_pkgs}",
            ],
        }

        self._run(test_target, expected, tools_config)

    def test_custom_env(self, tools_config):
        test_target = "customenv"
        expected = {
            "load": ["source /path/to/env/load.sh"],
            "unload": ["unloadenv"],
        }
        self._run(test_target, expected, tools_config)


class TestPackageToolScripts(BaseToolScriptsTest):
    section = "packages"

    def test_custom_pkg(self, tools_config, custom_script):
        test_target = "custompkg"
        expected = {
            "load": None,
            "unload": None,
            "setup": [
                f"mkdir -p {self.lib_dir}" + "/build/${ENV_NAME:-}",
                "# Post-script",
                f"{custom_script}",
                "ecflow_client --label=version $(if [[ -f version.txt ]]; then cat version.txt; else echo NA; fi)",
            ],
        }
        self._run(test_target, expected, tools_config)

    def test_literal_str_cmd(self, tools_config):
        test_target = "mypkg"
        pkg_src = tools_config["packages"][test_target]["source"]
        pre_script = tools_config["packages"][test_target]["pre_script"]
        post_script = tools_config["packages"][test_target]["post_script"]

        expected = {
            "load": None,
            "unload": None,
            "setup": [
                f"{pre_script}",
                f"mkdir -p {self.lib_dir}" + "/build/${ENV_NAME:-}",
                f"dest_dir={self.lib_dir}"
                + "/build/${ENV_NAME:-}"
                + f"/{test_target}",
                "rm -rf $dest_dir",
                "mkdir -p $dest_dir",
                f"scp {pkg_src}  $dest_dir/",
                "cd $dest_dir",
                "# Post-script",
                f"{post_script}",
                "ecflow_client --label=version $(if [[ -f version.txt ]]; then cat version.txt; else echo NA; fi)",
            ],
        }
        self._run(test_target, expected, tools_config)

    def test_rsync_and_literal_installer(self, tools_config):
        test_target = "myremotepkg"
        pkg_src = tools_config["packages"][test_target]["source"]
        cmd = tools_config["packages"][test_target]["post_script"]

        expected = {
            "load": None,
            "unload": None,
            "setup": [
                f"mkdir -p {self.lib_dir}" + "/build/${ENV_NAME:-}",
                f"dest_dir={self.lib_dir}"
                + "/build/${ENV_NAME:-}"
                + f"/{test_target}",
                f"rsync -avzpL {pkg_src}  $dest_dir/",
                "# Post-script",
                f"{cmd}",
                "ecflow_client --label=version $(if [[ -f version.txt ]]; then cat version.txt; else echo NA; fi)",
            ],
        }

        self._run(test_target, expected, tools_config)

    def test_link_and_list_commands(self, tools_config):
        test_target = "dev-install"
        pkg_src = tools_config["packages"][test_target]["source"]
        run_cmd_list = tools_config["packages"][test_target]["post_script"]

        expected = {
            "load": None,
            "unload": None,
            "setup": [
                f"mkdir -p {self.lib_dir}" + "/build/${ENV_NAME:-}",
                f"dest_dir={self.lib_dir}"
                + "/build/${ENV_NAME:-}"
                + f"/{test_target}",
                "rm -rf $dest_dir",
                f"ln -sfn {pkg_src} $dest_dir",
                "if [[ -L $dest_dir && -d $(readlink $dest_dir) ]]; then",
                "    echo Link and directory exist",
                "else",
                "    echo Link or directory does not exist",
                "    exit 1",
                "fi",
                "cd $dest_dir",
                "# Post-script",
                *run_cmd_list,
                "ecflow_client --label=version $(if [[ -f version.txt ]]; then cat version.txt; else echo NA; fi)",
            ],
        }
        self._run(test_target, expected, tools_config)

    def test_git_and_file_installer(self, tools_config, custom_script):
        test_target = "earthkit"
        pkg_src = tools_config["packages"][test_target]["source"]
        branch = tools_config["packages"][test_target]["branch"]

        expected = {
            "load": None,
            "unload": None,
            "setup": [
                f"mkdir -p {self.lib_dir}" + "/build/${ENV_NAME:-}",
                f"dest_dir={self.lib_dir}"
                + "/build/${ENV_NAME:-}"
                + f"/{test_target}",
                "rm -rf $dest_dir",
                f"giturl={pkg_src}",
                f"gitbranch={branch}",
                "git clone $giturl --branch $gitbranch --single-branch --depth 1 $dest_dir",
                "cd $dest_dir",
                "# Post-script",
                f"{custom_script}",
                "ecflow_client --label=version $(if [[ -f version.txt ]]; then cat version.txt; else echo NA; fi)",
            ],
        }

        self._run(test_target, expected, tools_config)

    def test_git_custom_build_dir(self, tools_config, custom_script):
        test_target = "earthkit"
        pkg_src = tools_config["packages"][test_target]["source"]
        branch = tools_config["packages"][test_target]["branch"]
        build_dir = "/my/custom/build/dir"
        tools_config["packages"][test_target]["build_dir"] = build_dir

        expected = {
            "load": None,
            "unload": None,
            "setup": [
                f"mkdir -p {build_dir}",
                f"dest_dir={build_dir}/{test_target}",
                "rm -rf $dest_dir",
                f"giturl={pkg_src}",
                f"gitbranch={branch}",
                "git clone $giturl --branch $gitbranch --single-branch --depth 1 $dest_dir",
                "cd $dest_dir",
                "# Post-script",
                f"{custom_script}",
                "ecflow_client --label=version $(if [[ -f version.txt ]]; then cat version.txt; else echo NA; fi)",
            ],
        }

        self._run(test_target, expected, tools_config)
