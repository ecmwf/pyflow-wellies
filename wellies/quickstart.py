#!/usr/bin/env python3

import os
import stat
import sys
from argparse import ArgumentParser
from os import path
from pwd import getpwuid
from socket import gethostname
from typing import Dict, List

from jinja2 import Environment, PackageLoader

import wellies as wl

pw_user = getpwuid(os.getuid())

DEFAULTS = {
    "host": "localhost",
    "user": "{USER}",
    "author": pw_user.pw_gecos,
    "output_root": "{SCRATCH}",
    "deploy_root": "{PERM}/pyflow",
    "job_out": "%ECF_HOME%",
    "workdir": "$TMPDIR",
}


class PyflowSuiteRenderer:
    def __init__(self, extra_templatedir: str = "") -> None:
        self.alt_templates = extra_templatedir
        self.env = Environment(
            loader=PackageLoader("wellies", package_path="templates")
        )

    def get_template(self, template_name: str) -> str:
        return self.env.get_template(template_name)

    def render(self, template_name: str, context: Dict) -> str:
        # TODO: add extra loader based on custom templatedir.
        # if file found provide a new env pointing to that dir
        return self.env.get_template(template_name).render(context)

    def render_string(self, source, context: Dict) -> str:
        return self.env.from_string(source).render(context)

    @classmethod
    def render_from_file():
        pass


def start_project(options: Dict, overwrite: bool = False) -> None:
    """Generate project basic structure based on options."""

    def write_file(fpath: str, content: str) -> None:
        if overwrite or not path.isfile(fpath):
            print(f"Creating file {fpath}.")
            with open(fpath, "wt", encoding="utf-8") as f:
                f.write(content)
        else:
            print(f"File {fpath} already exists, skipping.")

    templatedir = options.get("templatedir")
    renderer = PyflowSuiteRenderer(templatedir)

    project = options.get("project")
    root_path = path.abspath(options["path"])
    options.setdefault("project_root", root_path)
    os.makedirs(root_path, exist_ok=True)

    out_root = options["output_root"]
    out_root = path.join(out_root, project)
    options["output_root"] = out_root

    options.setdefault("lib_dir", path.join("{output_root}", "local"))
    options.setdefault("data_dir", path.join("{output_root}", "data"))
    options.setdefault(
        "deploy_dir", path.join(options["deploy_root"], project)
    )
    options["localhost"] = gethostname()
    options["version"] = wl.__version__

    # write main executable file and Makefile
    suite_file = path.join(root_path, "deploy.py")
    write_file(suite_file, renderer.render("suite.py_t", options))
    st = os.stat(suite_file)
    os.chmod(suite_file, st.st_mode | stat.S_IEXEC)
    write_file(
        path.join(root_path, "Makefile"),
        renderer.render("Makefile_t", options),
    )

    # create suite folder containing nodes.py
    suite_dir = path.join(root_path, "suite")
    os.makedirs(suite_dir, exist_ok=True)

    write_file(
        path.join(suite_dir, "nodes.py"),
        renderer.render("nodes.py_t", options),
    )

    # create config folder containing yaml files
    config_dir = path.join(root_path, "configs")
    os.makedirs(config_dir, exist_ok=True)
    write_file(
        path.join(config_dir, "config.yaml"),
        renderer.render("config.yaml_t", options),
    )
    write_file(
        path.join(config_dir, "execution_contexts.yaml"),
        renderer.render("execution_contexts.yaml_t", options),
    )
    write_file(
        path.join(config_dir, "tools.yaml"),
        renderer.render("tools.yaml_t", options),
    )
    write_file(
        path.join(config_dir, "data.yaml"),
        renderer.render("data.yaml_t", options),
    )

    return None


def valid_dir(d: Dict) -> bool:
    root = d["path"]
    if not path.exists(root):
        return True
    if not path.isdir(root):
        return False

    reserved_names = [
        "configs",
        "suite",
        d["project"] + ".py",
    ]
    if set(reserved_names) & set(os.listdir(root)):
        return False

    return True


def ask_user(options: Dict) -> None:
    raise NotImplementedError("Interactive tool not implemented.")


def get_parser() -> ArgumentParser:
    description = (
        "\n"
        "Generate initial files on base structure for a pyflow suite project.\n"  # noqa: E501
        "\n"
        "wellies-quickstart is an interactive tool that asks some questions about your\n"  # noqa: E501
        "project and then generates a complete suite directory and sample\n"
        "definitions which can be deployed with pyflow.\n"
    )
    parser = ArgumentParser(
        usage="%(prog)s [OPTIONS] <PROJECT_DIR>", description=description
    )
    parser.add_argument(
        "path",
        metavar="PROJECT_DIR",
        default=".",
        nargs="?",
        help="project root",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        dest="interactive",
        default=None,
        help="interactive mode",
    )
    group = parser.add_argument_group("Project basic options")
    group.add_argument(
        "-p",
        "--project",
        metavar="PROJECT",
        dest="project",
        help="project name",
    )
    group.add_argument(
        "--author", metavar="AUTHOR", dest="author", help="project author"
    )

    group = parser.add_argument_group("Suite deployment options")
    group.add_argument(
        "--job_out",
        metavar="PATH",
        dest="job_out",
        help="Jog output directory",
    )
    group.add_argument(
        "-u", "--user", metavar="USER", dest="user", help="User"
    )
    group.add_argument(
        "--host", metavar="HOST", dest="host", help="Target host"
    )
    group.add_argument(
        "-o",
        "--output_root",
        metavar="PATH",
        dest="output_root",
        help="Suite output root path",
    )
    group.add_argument(
        "--deploy_root",
        metavar="PATH",
        dest="deploy_root",
        help="Suite deployment root path",
    )
    group = parser.add_argument_group("Project templating")
    group.add_argument(
        "-t",
        "--templatedir",
        metavar="TEMPLATEDIR",
        dest="templatedir",
        help="template directory for custom template files",
    )
    group.add_argument(
        "-d",
        metavar="NAME=VALUE",
        action="append",
        dest="variables",
        help="define a template variable",
    )

    return parser


# Main call
def main(argv: List[str] = sys.argv[1:]) -> int:
    parser = get_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as err:
        return err.code

    options = vars(args)
    # delete None values
    options = {k: v for k, v in options.items() if v is not None}
    try:
        if "interactive" in options:
            ask_user(options)
        elif {"project"}.issubset(options):
            # quiet mode with all required params satisfied, use default
            d2 = DEFAULTS.copy()
            d2.update(options)
            options = d2

            if not valid_dir(options):
                print()
                print(
                    "Error: specified path is not a directory,"
                    " or suite files already exist."
                )
                print(
                    "wellies-quickstart only generate into a empty directory."
                    " Please specify a new root path."
                )
                return 1
            if options["project"] in ["suite", "installers"]:
                print("invalid project name. Please select another one.")
                return 1
        else:
            print(
                'non-interactive mode, but any of "project" is not specified.'
            )
            return 1

    except (KeyboardInterrupt, EOFError):
        print()
        print("[Interrupted.]")
        return 130  # 128 + SIGINT

    for variable in options.get("variables", []):
        try:
            name, value = variable.split("=")
            options[name] = value
        except ValueError:
            print(f"Invalid template variable: {variable}")

    start_project(options, overwrite=False)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
