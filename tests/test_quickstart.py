# flake8: noqa
import os
import subprocess
import tempfile

from wellies.quickstart import main


def quickstart():
    suite_dir = tempfile.mkdtemp(prefix=f"test_suite_")
    deploy_dir = tempfile.mkdtemp(prefix=f"deploy_")
    main(
        [
            f"{suite_dir}",
            "-p",
            "test",
            "--deploy_root",
            deploy_dir,
            "--output_root",
            "/my/output/root",
        ]
    )
    print(suite_dir)
    print(os.listdir(suite_dir))
    print(os.listdir(os.path.join(suite_dir, "configs")))

    return suite_dir, deploy_dir


def test_quickstart():
    suite_dir, deploy_dir = quickstart()
    assert os.path.exists(os.path.join(suite_dir, "deploy.py"))


def test_quickstart_help():
    suite_dir, deploy_dir = quickstart()

    # test help
    subprocess.check_call([f"{suite_dir}/deploy.py", "--help"])


def test_quickstart_deploy():
    suite_dir, deploy_dir = quickstart()

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


def test_quickstart_tools():
    suite_dir, deploy_dir = quickstart()

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


def test_quickstart_exec_context():
    suite_dir, deploy_dir = quickstart()

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
