import os
import shutil
import tempfile
import warnings

import git
import pyflow as pf
import tracksuite as ts

import wellies as wl
from wellies import LOGGER as logger


def _generate_suite(suite, staging_dir, suite_name):
    """
    Generate a suite in a staging directory.
    """
    logger.info("Generating suite:")
    logger.info(f"    -> Deploying suite scripts in {staging_dir}")
    if os.path.isdir(staging_dir):
        shutil.rmtree(staging_dir)
    suite.deploy_suite(path=staging_dir)
    suite_def = suite.ecflow_definition()
    suite_def.check()
    def_file = os.path.join(staging_dir, f"{suite_name}.def")
    suite_def.save_as_defs(def_file)
    logger.info(f"    -> Definition file written in {def_file}")
    return def_file


def git_commit_message(message_args):
    """
    Generate a git commit message with additional repository information
    (directory, git remote, git hash).

    Parameters
    ----------
    message_args : str or None
        Additional message to append to the default commit message.
        If None, only the default message is used.
    Returns
    -------
    str
        The complete commit message including repository information and the
        additional message if provided.
    Notes
    -----
    The default message includes the version of the wellies suite and the
    current working directory.
    If a local git repository is found, the message also includes the remote
    repository name and the current commit hash.
    If no local git repository is found, only the default message is used.
    """

    default_message = (
        f"suite generated using wellies {wl.__version__}"
        + f" from directory {os.getcwd()}"
    )

    try:
        repo = git.Repo(".")

        # local commit info
        commit_hash = repo.head.commit.hexsha
        # get local remote info
        remotes = [rem.name for rem in repo.remotes]
        base_remote = "origin" if "origin" in remotes else remotes[:1]
        if base_remote:
            remote_url = next(repo.remote(base_remote).urls)
        else:
            warnings.warn("No remotes found in deployment source git repo")
            remote_url = "N/D"
            base_remote = ""

        # get local branch info
        if repo.head.is_detached:
            branch_name = "Detached HEAD"
        else:
            branch_name = repo.active_branch.name

        default_message += "\nGit info:\n"
        default_message += f"  - Remote URL: {base_remote}:{remote_url} \n"
        default_message += f"  - Commit: {commit_hash}\n"
        default_message += f"  - Branch: {branch_name}\n"
        if repo.is_dirty():
            modified_files = [item.a_path for item in repo.index.diff(None)]
            if modified_files:
                default_message += "  - Local changes:\n"
                for file in modified_files:
                    default_message += f"    - {file}\n"
    except (
        git.exc.NoSuchPathError,
        git.exc.InvalidGitRepositoryError,
        ValueError,
    ):
        logger.info(
            "Could not find local git repository, using default message"
        )

    if message_args is None:
        message = default_message
    else:
        message = default_message + "\n\n" + {message}

    return message


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

    logger.info("------------------------------------------------------")
    logger.info(f"Staging suite to {build_dir}")
    logger.info("------------------------------------------------------")
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
                logger.error("Aborting deployment")
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
        logger.info("------------------------------------------------------")
        logger.info(f"Deploying suite to {target_repo}")
        logger.info("------------------------------------------------------")
        if files is not None:
            logger.info("Deploying only the following files:")
            for f in files:
                logger.info(f"    - {f}")
        if not no_prompt:
            check = input(
                "You are about to push the staged suite to the target directory. Are you sure? (N/y)"  # noqa: E501
            )
            if check != "y":
                logger.info("Aborting deployment")
                exit(1)

        message = git_commit_message(message)

        if deployer.deploy(message, files):
            logger.info(f"Suite deployed to {target_repo}")
            logger.info(f"Definition file: {target_repo}/{name}.def")
    else:
        logger.info("No deploy option activated. Deployment aborted")
