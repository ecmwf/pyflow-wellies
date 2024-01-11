import os
import shutil
import tempfile

import git
import pyflow as pf
import tracksuite as ts

import wellies as wl


def _generate_suite(suite, staging_dir, suite_name):
    """
    Generate a suite in a staging directory.
    """
    print("Generating suite:")
    print(f"    -> Deploying suite scripts in {staging_dir}")
    if os.path.isdir(staging_dir):
        shutil.rmtree(staging_dir)
    suite.deploy_suite(path=staging_dir)
    suite_def = suite.ecflow_definition()
    suite_def.check()
    def_file = os.path.join(staging_dir, f"{suite_name}.def")
    suite_def.save_as_defs(def_file)
    print(f"    -> Definition file written in {def_file}")
    return def_file


def deploy_suite(
    suite: pf.Suite,
    user: str,
    name: str,
    hostname: str,
    deploy_dir: str,
    backup_deploy: str = None,
    build_dir: str = None,
    no_prompt: bool = False,
    no_deploy: bool = False,
    message: str = None,
    files: list = None,
):
    """
    Deploy a suite to a remote repository.

    Parameters
    ----------
        suite (dict):
            The suite to deploy.
        user (str):
            The username to use for the deployment.
        name (str):
            The name of the suite.
        hostname (str):
            The hostname of the remote repository.
        deploy_dir (str):
            The target to deploy the suite to.
        backup_deploy (str, optional):
            The backup repository to use. Defaults to None.
        build_dir (str, optional):
            The build directory to use. If None, a temporary
            directory will be created. Defaults to None.
        no_prompt (bool, optional):
            Skip all prompts and answer yes to all. Defaults to False.
        no_deploy (bool, optional):
            Whether to skip the deployment. Defaults to False.
        message (str, optional):
            The commit message to use for the deployment. Defaults to None.
        files (list, optional):
            The files to deploy. If None, everything is deployed.
            Defaults to None.
    """
    if build_dir is None:
        build_dir = tempfile.mkdtemp(prefix=f"build_{name}_")

    print("------------------------------------------------------")
    print(f"Staging suite to {build_dir}")
    print("------------------------------------------------------")
    build_dir = os.path.realpath(build_dir)
    staging_dir = os.path.join(build_dir, "staging")
    local_repo = os.path.join(build_dir, "local")
    target_repo = deploy_dir

    _generate_suite(suite, staging_dir, name)

    try:
        deployer = ts.GitDeployment(
            host=hostname,
            user=user,
            staging_dir=staging_dir,
            local_repo=local_repo,
            target_repo=target_repo,
            backup_repo=backup_deploy,
        )
    except git.exc.GitCommandError:
        if not no_prompt:
            check = input(
                "Remote repository does not seem to exist. Do you want to initialise it? (N/y)"  # noqa: E501
            )
            if check != "y":
                print("Aborting deployment")
                exit(1)
        ts.setup_remote(
            hostname, user, target_repo, remote=backup_deploy, force=True
        )
        deployer = ts.GitDeployment(
            host=hostname,
            user=user,
            staging_dir=staging_dir,
            local_repo=local_repo,
            target_repo=target_repo,
            backup_repo=backup_deploy,
        )
    deployer.pull_remotes()
    deployer.diff_staging()

    if not no_deploy:
        print("------------------------------------------------------")
        print(f"Deploying suite to {target_repo}")
        print("------------------------------------------------------")
        if files is not None:
            print("Deploying only the following files:")
            for f in files:
                print(f"    - {f}")
        if not no_prompt:
            check = input(
                "You are about to push the staged suite to the target directory. Are you sure? (N/y)"  # noqa: E501
            )
            if check != "y":
                print("Aborting deployment")
                exit(1)
        default_message = (
            f"suite generated using wellies {wl.__version__}"
            + f" from directory {os.getcwd()}"
        )
        if message is None:
            message = default_message
        else:
            message = default_message + "\n" + {message}
        if deployer.deploy(message, files):
            print(f"Suite deployed to {target_repo}")
            print(f"Definition file: {target_repo}/{name}.def")
    else:
        print("No deploy option activated. Deployment aborted")
