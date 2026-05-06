# flake8: noqa
import os
import subprocess


def test_quickstart(quickstart):
    suite_dir, deploy_dir = quickstart
    assert os.path.exists(os.path.join(suite_dir, "deploy.py"))


def test_quickstart_help(quickstart):
    suite_dir, deploy_dir = quickstart

    # test help
    subprocess.check_call([f"{suite_dir}/deploy.py", "--help"])


def test_quickstart_deploy(quickstart):
    suite_dir, deploy_dir = quickstart

    # test deployment
    subprocess.check_call(
        [
            f"{suite_dir}/deploy.py",
            "user",
            "-p",
            "profiles.yaml",
            "-y",
        ],
        cwd=suite_dir,
    )

    def_file = os.path.join(deploy_dir, "my_suite", "my_suite.def")
    assert os.path.exists(def_file)


def test_quickstart_tools_nohost_fails(quickstart):

    suite_dir, deploy_dir = quickstart

    failing_config = (
        "\nmissing_host:\n    - configs/user.yaml\n    - configs/tools.yaml\n"
    )

    with open(os.path.join(suite_dir, "profiles.yaml"), "a") as fin:
        fin.write("\n" + failing_config)

    # test deployment
    try:
        subprocess.run(
            [
                f"{suite_dir}/deploy.py",
                "missing_host",
                "-y",
            ],
            cwd=suite_dir,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        assert b"WelliesConfigurationError" in exc.stderr
    else:
        raise Exception("This test should have failed")


def test_quickstart_no_optional_files(quickstart):
    """Without optional flags, optional components should not be generated."""
    suite_dir, deploy_dir = quickstart
    assert not os.path.exists(os.path.join(suite_dir, ".vscode"))
    assert not os.path.exists(os.path.join(suite_dir, "snippets"))
    assert not os.path.exists(os.path.join(suite_dir, "src"))
    assert not os.path.exists(os.path.join(suite_dir, "manuals"))
    assert not os.path.exists(os.path.join(suite_dir, ".gitignore"))
    assert not os.path.exists(os.path.join(suite_dir, "pyproject.toml"))
    assert not os.path.exists(os.path.join(suite_dir, "configs", "src.yaml"))


def test_quickstart_vscode(quickstart_vscode):
    """--vscode flag should generate .vscode/launch.json and .vscode/tasks.json."""
    suite_dir, deploy_dir = quickstart_vscode
    vscode_dir = os.path.join(suite_dir, ".vscode")
    assert os.path.exists(vscode_dir)
    launch_json = os.path.join(vscode_dir, "launch.json")
    tasks_json = os.path.join(vscode_dir, "tasks.json")
    assert os.path.exists(launch_json)
    assert os.path.exists(tasks_json)
    # Verify VSCode env var syntax is used (not literal {HOME})
    with open(launch_json) as f:
        content = f.read()
    assert (
        "${env:" in content
    ), "VSCode env var syntax ${env:VAR} should be present in launch.json"
    assert (
        "{HOME}" not in content
    ), "Raw {HOME} should not appear in launch.json"
    # Verify no hardcoded home directory paths leaked into the config
    home = os.environ.get("HOME", "")
    if home:
        assert (
            home not in content
        ), f"Hardcoded home path {home} should not appear in launch.json"


def test_quickstart_full(quickstart_full):
    """--full flag should generate all optional components."""
    suite_dir, deploy_dir = quickstart_full
    assert os.path.exists(os.path.join(suite_dir, "snippets"))
    assert os.path.exists(os.path.join(suite_dir, "src"))
    assert os.path.exists(os.path.join(suite_dir, "manuals"))
    assert os.path.exists(os.path.join(suite_dir, ".gitignore"))
    assert os.path.exists(os.path.join(suite_dir, "pyproject.toml"))
    assert os.path.exists(os.path.join(suite_dir, "configs", "src.yaml"))
