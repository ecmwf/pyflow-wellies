from dataclasses import dataclass
from os.path import join as pjoin

import pyflow as pf
import pytest
import yaml

import wellies as wl
from wellies.quickstart import main


@dataclass
class WelliesTestHost:
    host: pf.Host
    defaults: dict


@pytest.fixture
def custom_script():
    return "echo 'custom installer script'"


@pytest.fixture
def custom_script_file(tmp_path, custom_script):
    custom_installer = tmp_path.joinpath("installer.sh").as_posix()
    with open(custom_installer, "w") as finst:
        finst.write(custom_script + "\n")
    return custom_installer


@pytest.fixture
def tools_config(custom_script_file):
    config_in = {
        "modules": {
            "conda": {
                "version": "default",
            },
            "python": {
                "name": "python3",
                "version": "3.10.10-01",
            },
            "netcdf4": {
                "depends": ["python"],
            },
            "prgenv/intel": {},
            "privatemodule": {"modulefiles": "/path/to/modulefiles"},
        },
        "packages": {
            "mypkg": {
                "pre_script": "cd /path/to/pkg/src; cd -",
                "type": "copy",
                "source": "/path/to/pkg/src",
                "post_script": "echo literal script as string",
            },
            "myremotepkg": {
                "type": "rsync",
                "source": "hpc-login:/path/to/pkg/src",
                "post_script": "make .",
            },
            "earthkit": {
                "type": "git",
                "source": "git@github.com:ecmwf/earthkit-data.git",
                "branch": "develop",
                "post_script": f"{custom_script_file}",
            },
            "dev-install": {
                "type": "link",
                "source": "/path/to/pkg/src",
                "post_script": [
                    "# literal script as list",
                    "pip install . -e --no-deps",
                    "pip show src | grep Version > version.txt",
                ],
            },
            "custompkg": {
                "type": "custom",
                "post_script": f"{custom_script_file}",
            },
        },
        "env_variables": {
            "pypath": {
                "variable": "PYTHONPATH",
                "value": "$LIB_DIR/bin:$LIB_DIR/python",
            },
            "OMP_PLACES": {
                "value": "threads",
            },
        },
        "environments": {
            "bin": {
                "type": "folder",
                "depends": ["pypath"],
            },
            "myenv1": {
                "type": "system_venv",
                "depends": ["python", "netcdf4"],
                "packages": ["earthkit"],
                "extra_packages": ["python==3.10", "pandas>2", "xarray"],
            },
            "venv": {
                "type": "venv",
                "packages": ["earthkit"],
                "env_file": {
                    "type": "rsync",
                    "source": "/path/to/env",
                    "files": "file.txt",
                    "rsync_options": ["--chmod ug+rwx,o+r"],
                },
            },
            "anemoi_venv": {
                "type": "venv",
                "packages": ["anemoi_datasets"],
                "depends": ["python"],
            },
            "conda_exist": {
                "type": "conda",
                "environment": "/path/to/conda/env",
            },
            "conda_copy": {
                "type": "conda",
                "depends": ["conda"],
                "env_file": {
                    "type": "copy",
                    "source": "/path/to/project",
                    "files": "environment.yaml",
                },
            },
            "conda_pkgs": {
                "type": "conda",
                "depends": ["conda"],
                "packages": ["earthkit"],
                "extra_packages": ["python==3.10", "pcraster>=4.3.0", "gdal"],
                "conda_cmd": "mamba -c conda-forge",
            },
            "conda_remote_file": {
                "type": "conda",
                "packages": ["earthkit"],
                "depends": ["conda"],
                "env_file": {
                    "type": "git",
                    "source": "ssh://git.ecmwf.int/cefl/condaenvs.git",
                    "branch": "master",
                    "files": "environment.yaml",
                },
            },
            "customenv": {
                "type": "custom",
                "load": "source /path/to/env/load.sh",
                "unload": "unloadenv",
            },
        },
    }

    return config_in


@pytest.fixture
def tools_file(tmp_path, tools_config):
    fpath = tmp_path.joinpath("tools.yaml").as_posix()
    with open(fpath, "w") as fout:
        fout.write(yaml.dump(tools_config))
    return fpath


@pytest.fixture
def slurmhost_config():
    config_in = dict(
        host=dict(
            hostname="slurm",
            user="beans",
            ecflow_path="/usr/bin/ecflow_client",
            submit_arguments=dict(
                defaults=dict(
                    job_name="%TASK%",
                    account="project",
                ),
                serial=dict(
                    queue="q1",
                    total_tasks=1,
                ),
                parallel=dict(
                    queue="qp",
                ),
            ),
        )
    )

    return config_in


@pytest.fixture
def wlhost(slurmhost_config):
    host, defaults = wl.get_host(**slurmhost_config["host"])
    return WelliesTestHost(host, defaults)


@pytest.fixture
def quickstart(tmpdir):
    suite_dir = pjoin(tmpdir, "my-suite-path")
    deploy_dir = pjoin(tmpdir, "deploy")

    main(
        [
            "my-suite",
            "-p",
            f"{suite_dir}",
            "--deploy_root",
            str(deploy_dir),
            "--output_root",
            "/my/output/root",
            "--host",
            "localhost",
        ]
    )

    return suite_dir, deploy_dir


@pytest.fixture
def quickstart_local_git(quickstart, request):

    import git

    suite_dir, deploy_dir = quickstart

    repo = git.Repo.init(suite_dir)
    repo.create_remote("origin", "ssh://git@git.test.repo")
    repo.index.add("*")
    repo.index.commit(f"Initial commit done for test {request.node.name}")

    return suite_dir, deploy_dir
