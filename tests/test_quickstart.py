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
