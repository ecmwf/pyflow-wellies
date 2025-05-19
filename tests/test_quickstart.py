# flake8: noqa
import os
import subprocess

import pytest

from wellies.quickstart import main


@pytest.fixture
def quickstart_dirs(tmp_path):
    """Generate a temporary quickstart project for the tests."""

    suite_dir = tmp_path.joinpath("suite_dir")
    deploy_dir = tmp_path.joinpath("deploy_dir")
    suite_dir.mkdir()
    deploy_dir.mkdir()

    main(
        [
            str(suite_dir),
            "-p",
            "test",
            "--deploy_root",
            str(deploy_dir),
            "--output_root",
            "/my/output/root",
        ]
    )

    yield str(suite_dir), str(deploy_dir)


def test_quickstart(quickstart_dirs):
    suite_dir, deploy_dir = quickstart_dirs
    assert os.path.exists(os.path.join(suite_dir, "deploy.py"))


def test_quickstart_help(quickstart_dirs):
    suite_dir, _ = quickstart_dirs

    # test help
    subprocess.check_call([f"{suite_dir}/deploy.py", "--help"])


def test_quickstart_deploy(quickstart_dirs):
    suite_dir, deploy_dir = quickstart_dirs

    # test deployment
    subprocess.check_call(
        [
            f"{suite_dir}/deploy.py",
            os.path.join(suite_dir, "configs", "config.yaml"),
            "-y",
        ]
    )

    def_file = os.path.join(deploy_dir, "test", "test.def")
    assert os.path.exists(def_file)


def test_quickstart_tools(quickstart_dirs):
    suite_dir, deploy_dir = quickstart_dirs

    # test deployment
    subprocess.check_call(
        [
            f"{suite_dir}/deploy.py",
            os.path.join(suite_dir, "configs", "config.yaml"),
            os.path.join(suite_dir, "configs", "tools.yaml"),
            "-y",
        ]
    )

    def_file = os.path.join(deploy_dir, "test", "test.def")
    assert os.path.exists(def_file)


def test_quickstart_exec_context(quickstart_dirs):
    suite_dir, deploy_dir = quickstart_dirs

    # test deployment
    subprocess.check_call(
        [
            f"{suite_dir}/deploy.py",
            os.path.join(suite_dir, "configs", "config.yaml"),
            os.path.join(suite_dir, "configs", "execution_contexts.yaml"),
            "-y",
        ]
    )

    def_file = os.path.join(deploy_dir, "test", "test.def")
    assert os.path.exists(def_file)
