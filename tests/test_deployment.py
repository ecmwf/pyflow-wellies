import os
import re
import subprocess
from os.path import join as pjoin

import git
import pytest

from wellies.deployment import git_commit_message


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


@pytest.fixture
def git_repo(tmp_path):
    repo = git.Repo.init(tmp_path)
    (tmp_path / "suite").mkdir()
    (tmp_path / "suite" / "deploy.py").write_text("")
    repo.index.add(["suite/deploy.py"])
    repo.index.commit("Initial commit")
    return repo


def test_git_commit_message_from_subdirectory(git_repo, monkeypatch):
    git_repo.create_remote("origin", "ssh://git@git.test.repo")
    suite_dir = os.path.join(git_repo.working_tree_dir, "suite")
    monkeypatch.chdir(suite_dir)

    message = git_commit_message(None)

    assert f"from directory {suite_dir}" in message
    assert "Remote URL: origin:ssh://git@git.test.repo" in message
    assert f"Commit: {git_repo.head.commit.hexsha}" in message


def test_git_commit_message_local_changes(git_repo, monkeypatch):
    suite_dir = os.path.join(git_repo.working_tree_dir, "suite")
    with open(os.path.join(suite_dir, "deploy.py"), "w") as f:
        f.write("# modified")
    monkeypatch.chdir(suite_dir)

    message = git_commit_message(None)

    assert "Local changes:\n    - suite/deploy.py" in message


def test_git_commit_message_non_origin_remote(git_repo, monkeypatch):
    git_repo.create_remote("upstream", "ssh://git@git.upstream.repo")
    monkeypatch.chdir(git_repo.working_tree_dir)

    message = git_commit_message(None)

    assert "Remote URL: upstream:ssh://git@git.upstream.repo" in message


def test_git_commit_message_extra_message(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo.working_tree_dir)

    message = git_commit_message("my custom message")

    assert "Git info:" in message
    assert message.endswith("\n\nmy custom message")


def test_git_commit_message_no_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    message = git_commit_message(None)

    assert f"from directory {tmp_path}" in message
    assert "Git info:" not in message
