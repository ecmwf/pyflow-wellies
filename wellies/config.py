import os
import re
from argparse import ArgumentParser
from collections import abc
from datetime import datetime
from datetime import timedelta
from string import Formatter
from typing import Optional

import yaml

from wellies.exceptions import WelliesConfigurationError


def get_parser() -> ArgumentParser:
    """
    Create the default wellies argument parser.

    Returns:
    ArgumentParser: An ArgumentParser object including the wellies options.
    """
    description = (
        "\n" "Generate required files for a pyflow suite project." "\n"
    )
    parser = ArgumentParser(
        usage="%(prog)s <PROFILE>",
        description=description,
    )
    parser.add_argument(
        "name",
        metavar="PROFILE",
        help="YAML configuration profile name",
    )
    parser.add_argument(
        "-p",
        "--profiles",
        default="profiles.yaml",
        metavar="CONFIG_NAME",
        help="YAML configuration profiles ",
    )
    parser.add_argument(
        "-s",
        "--set",
        metavar="KEY=VALUE",
        nargs="+",
        help="Set a number of key-value pairs "
        "(do not put spaces before or after the = sign). "
        "If a value contains spaces, you should define "
        "it with double quotes: "
        'foo="this is a sentence". Note that '
        "values are always treated as strings.",
    )
    parser.add_argument(
        "-m",
        "--message",
        help="Deployment git commit message",
    )
    parser.add_argument(
        "-b",
        "--build_dir",
        help="Build directory for suite deployment, by default a temporary directory is created",  # noqa: E501
    )
    parser.add_argument(
        "-f",
        "--files",
        nargs="+",
        help="Specific files to deploy, by default everything is deployed",
    )
    parser.add_argument(
        "-y",
        help="Answers yes to all prompts",
        action="store_true",
    )
    parser.add_argument(
        "-n",
        "--no_deploy",
        help="Skip deployment",
        action="store_true",
    )
    parser.add_argument(
        "--log_level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level for the suite deployment",
    )
    return parser


def get_config_files(config_name: str, configs_file: str) -> list:
    """
    Get the list of configuration files to be used for the suite.

    Parameters
    ----------
    config_name : str
        The name of the configuration to be used.
    configs_file : str
        The path to the YAML file containing the configurations.

    Returns
    -------
    list
        A list of configuration files to be used.
    """
    with open(configs_file, "r") as file:
        configs = yaml.load(file, Loader=yaml.SafeLoader)

    if config_name not in configs:
        raise KeyError(
            f"Configuration '{config_name}' not found in {configs_file}"
        )

    return configs[config_name]


def parse_profiles(
    profiles_file: str, config_name: str, set_variables=None, global_vars=None
) -> dict:
    """
    Selects the group of files to read, as defined in a main deployments
    definition. Return the options from the concatenated files in the profiles.
    This integrates well with wellies command line option `-s` to do
    variable substitution.
    """

    # selects files to actually read
    config_files = get_config_files(config_name, profiles_file)

    # concatenate all yaml files into one dict
    options = parse_yaml_files(config_files, set_variables, global_vars)

    return options


def parse_yaml_files(
    config_files: list, set_variables=None, global_vars=None
) -> dict:
    """
    Concatenates the config dictionaries and check for duplicates
    Override values in files with entries given on set_variables.
    """

    # concatenate all yaml files into one dict
    options = concatenate_yaml_files(config_files)

    # replace entries given on command line
    options = overwrite_entries(options, set_variables)

    # subsitute variables
    options = substitute_variables(options, global_vars)

    validate_main_keys(options)

    return options


def overwrite_entries(options, set_values):
    if set_values:
        values_to_set = parse_vars(set_values)
        for key, value in values_to_set.items():
            nested_set(options, key.split("."), value)
    return options


def concatenate_yaml_files(yaml_files):
    options = {}
    concat_options = {}
    accepted_concatenation = ["ecflow_variables"]
    for yaml_path in yaml_files:
        with open(yaml_path, "r") as file:
            local_options = yaml.load(file, Loader=yaml.SafeLoader)

        # concatenated first
        for key in accepted_concatenation:
            if key in local_options:
                concat_options[key] = {
                    **concat_options.get(key, {}),
                    **local_options.pop(key),
                }

        # check for duplicates
        duplicated_keys = []
        for key in local_options.keys():
            if options.get(key) is not None:
                duplicated_keys.append(key)
        if duplicated_keys:
            raise KeyError(
                f"Following keys found in {yaml_path} already exist in config: {duplicated_keys}"  # noqa: E501
            )

        options.update(local_options)
        options.update(concat_options)
    return options


def parse_vars(items):
    """
    Parse a series of key-value pairs and return a dictionary
    """
    return dict(map(lambda s: s.split("="), items))


def nested_set(dic, keys, value):
    """
    Set the values from a nested dictionnary using a list of keys
    """
    for key in keys[:-1]:
        dic = dic[key]
    val_in_dic = dic.get(keys[-1], None)
    val_type = type(val_in_dic) if val_in_dic else None
    dic[keys[-1]] = val_type(value)


_ENV_VARS = [
    "USER",
    "HOME",
    "PERM",
    "HPCPERM",
    "SCRATCH",
    "PWD",
    "_FORTESTING",
]


def get_user_globals():
    now = datetime.now()

    global_vars = {}

    for var in _ENV_VARS:
        global_vars[var] = os.path.expandvars(f"${var}")

    global_vars["TODAY"] = now.strftime("%Y%m%d")
    global_vars["YESTERDAY"] = (now - timedelta(days=1)).strftime("%Y%m%d")

    return global_vars


class TemplateFormatter(Formatter):
    """String formatter class to override python built-in format specs."""

    def parse(self, format_string):
        """Overrides string.Formatter token parsing to ignore bash
        environment variables defined in the form ${VARNAME}."""
        bash_var_name = r"\$\{(.*)\:"
        bash_var_label = r"(\$\{.*\})"
        varnames = re.findall(bash_var_name, format_string)
        varlabels = re.findall(bash_var_label, format_string)
        for literal_text, field_name, format_spec, conversion in super().parse(
            format_string
        ):
            if field_name in varnames:
                yield literal_text.strip(r"$") + varlabels[
                    varnames.index(field_name)
                ], None, None, None
            else:
                yield literal_text, field_name, format_spec, conversion


def check_environment_variables_substitution(value: str) -> None:
    """Checks if environment variables are defined in the keys to format
    and make sure they exist in the environment.

    Parameters
    ----------
    value : str
        The string to check for environment variables

    Raises
    ------
    ValueError
        If an environment variable to be substituted is not set
    """

    keys_to_format = re.findall(r"\{(.+?)\}", value)
    for key in keys_to_format:
        if key in _ENV_VARS:
            if key not in os.environ:
                raise ValueError(f"Environment variable {key} is not set")


def substitute_variables(
    options: dict, globals: Optional[dict] = None
) -> dict:
    """Parse base configuration file using the keys on that same file to
    string format other values.
    Replaced variables will always be of type string.

    Parameters
    ----------
        options : dict
            submit_arguments configuration dictionary (from yaml file)
        globals: dict, default=None
            A dictionary with globals key-value pairs to use on the string
            format substitution to be performed on the file content.
            New local assignments will take prevalence.
    Returns
    -------
        dict: A dictionary with all variables substituted.

    :Attention: Does not support Lists

    TODO: support variable substitution inside Lists

    Raise: KeyError
        If key used before set.

    """

    def update(tree, newMapping=None):
        formatter = TemplateFormatter()
        if newMapping is None:
            newMapping = {}
        for key, value in tree.items():
            if isinstance(value, abc.Mapping):
                update(tree.get(key, {}), newMapping)
            else:
                if isinstance(value, str):
                    try:
                        check_environment_variables_substitution(value)
                        new = formatter.format(value, **newMapping)
                    except KeyError as err:
                        missing = err.args[0]
                        raise KeyError(
                            f'Variable substitution failed: Key "{missing}" used before assignment'  # noqa: E501
                        )
                else:
                    new = value
                newMapping[key] = new
                tree[key] = new
        return tree

    global_subs = get_user_globals()
    if globals is not None:
        global_subs.update(globals)

    return update(options, global_subs)


def parse_submit_arguments(options: dict) -> tuple:
    """Parse submission arguments to be used on [pyflow.Task][]
    definitions.

    If a `defaults` mapping is defined it will be used as a default
    definition for all other mappings defined.

    :Attention: "defaults" can't be used as a context key name.

    Parameters
    ----------
    options : dict
        submit_arguments configuration dictionary (from yaml file)

    Returns
    -------
    submit_arguments, submit_arguments_defaults : dict, dict
        Return parsed options as two dictionaries. The base submit arguments
        and a second one with the defaults options in a compatible format
        to be passed to a pyflow.Node variables argument.
    """
    PROTECTED = ["sthost"]
    replacements = {"tmpdir": "ssdtmp"}
    default_vars = {}
    if options:
        # remove global special key and add global values
        # to each defined context
        global_rsrc = options.pop("defaults", {})
        for ctx, resources in options.items():
            new = global_rsrc.copy()
            new.update(resources)
            options[ctx] = new

        # remove STHOST. We don't want to create new var at the suite level
        for prt in PROTECTED:
            global_rsrc.pop(prt, {})
        # replace other protected names for new safe variable names
        new = {}
        for name, val in global_rsrc.items():
            if name.lower() in replacements:
                new[replacements[name.lower()]] = val
            else:
                new[name] = val
        default_vars = {k.upper(): v for k, v in new.items()}

    return options, default_vars


def validate_main_keys(options: dict) -> bool:

    required = ["host", "ecflow_server"]

    for entry in required:
        if entry not in options:
            raise WelliesConfigurationError(
                f"Configs must include a '{entry}' entry. "
                "Check the documentation for more information"
            )
