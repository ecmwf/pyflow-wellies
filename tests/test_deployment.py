import os
import re
import subprocess
from os.path import join as pjoin

import git


def test_deploy_message(quickstart_local_git):
    suite_dir, deploy_dir = quickstart_local_git

    # test deployment
    ret = subprocess.run(
        [
            f"{suite_dir}/deploy.py",
            "user",
            "-p",
            "profiles.yaml",
            "-y",
        ],
        cwd=suite_dir,
        capture_output=True,
    )

    assert (
        ret.returncode == 0
    ), f"Deploy command failed with message {ret.stderr}"
    def_file = pjoin(deploy_dir, "my_suite", "my_suite.def")

    assert os.path.exists(def_file), f"{def_file} not found in deploy location"

    deployed_repo = git.Repo(pjoin(deploy_dir, "my_suite"))
    dev_repo = git.Repo(suite_dir)
    head_mess = deployed_repo.heads[0].commit.message

    assert "Remote URL: origin:ssh://git@git.test.repo" in head_mess
    assert f"from directory {suite_dir}" in head_mess
    commit_hash_in_message = re.search(r"Commit:\s*([a-fA-F0-9]+)", head_mess)
    assert commit_hash_in_message, "Commit hash not found in commit message"
    commit_hash = commit_hash_in_message.group(1)
    assert (
        commit_hash == dev_repo.heads[0].commit.hexsha
    ), "Local commit hash does not match the one in the deployed repository"


def test_deploy_warn_if_no_remotes(quickstart_local_git):
    suite_dir, deploy_dir = quickstart_local_git

    local_repo = git.Repo(suite_dir)
    local_repo.delete_remote("origin")

    # test deployment
    ret = subprocess.run(
        [
            f"{suite_dir}/deploy.py",
            "user",
            "-p",
            "profiles.yaml",
            "-y",
        ],
        cwd=suite_dir,
        capture_output=True,
    )

    assert (
        ret.returncode == 0
    ), f"Deploy command failed with message {ret.stderr}"
    def_file = pjoin(deploy_dir, "my_suite", "my_suite.def")

    assert os.path.exists(def_file), f"{def_file} not found in deploy location"

    assert (
        "No remotes found in deployment source git repo" in ret.stderr.decode()
    ), "Warning about no remotes not found in stderr"
