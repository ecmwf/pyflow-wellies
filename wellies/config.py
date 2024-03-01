import os
import re
from argparse import ArgumentParser
from collections import abc
from datetime import datetime, timedelta
from string import Formatter

import yaml


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
        usage="%(prog)s <CONFIG_FILE>",
        description=description,
    )
    parser.add_argument(
        "config_files",
        nargs="+",
        metavar="CONFIG_FILES",
        help="YAML configuration files path (order is important)",
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
    return parser


def parse_yaml_files(config_files, set_variables=None, global_vars=None):
    """
    Concatenates the config dictionaries and check for duplicates
    Override values in files with entries given on set_variables.
    This integrates well with wellies command line option `-s` to do
    variable substitution.

    Example
    -------

    >>> deploy.py config.yml -s host=localhost

    """

    # concatenate all yaml files into one dict
    options = concatenate_yaml_files(config_files)

    # replace entries given on command line
    options = overwrite_entries(options, set_variables)

    # subsitute variables
    options = substitute_variables(options, global_vars)

    return options


def overwrite_entries(options, set_values):
    if set_values:
        values_to_set = parse_vars(set_values)
        for key, value in values_to_set.items():
            nested_set(options, key.split("."), value)
    return options


def concatenate_yaml_files(yaml_files):
    options = {}
    for yaml_path in yaml_files:
        with open(yaml_path, "r") as file:
            local_options = yaml.load(file, Loader=yaml.SafeLoader)

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


def get_user_globals():
    now = datetime.now()
    global_vars = {
        "USER": os.path.expandvars("$USER"),
        "HOME": os.path.expandvars("$HOME"),
        "PERM": os.path.expandvars("$PERM"),
        "HPCPERM": os.path.expandvars("$HPCPERM"),
        "SCRATCH": os.path.expandvars("$SCRATCH"),
        "PWD": os.path.expandvars("$PWD"),
        "TODAY": now.strftime("%Y%m%d"),
        "YESTERDAY": (now - timedelta(days=1)).strftime("%Y%m%d"),
    }
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


def substitute_variables(options, globals=None):
    """parse base configuration file using the keys on that same file to
    string format other values.
    Replaced variables will always be of type string.

    Parameters
    ----------
        options : dict
            execution_contexts configuration dictionnary (from yaml file)
        globals: dict, default=None
            A dictionary with globals key-value pairs to use on the string
            format substitution to be performed on the file content.
            New local assignments will take prevalence.

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


def parse_execution_contexts(options):
    """parse execution context configuration file.
    Expects a global `execution_contexts` mapping with other mappings
    that define submit_arguments to be used on [pyflow.Task][]
    definitions.

    If a `defaults` mapping is defined it will be used as a default
    definition for all other mappings defined.

    :Attention: "defaults" can't be used as a context key name.

    Parameters
    ----------
    options : dict
        execution_contexts configuration dictionnary (from yaml file)

    Returns
    -------
    execution_contexts, submit_arguments_defaults : dict, dict
        Return parsed options as two dictionaries. The base execution contexts
        and a second one with the defaults options in a compatible format
        to be passed to a pyflow.Node variables argument.
    """
    PROTECTED=['sthost']
    replacements = {"tmpdir": "ssdtmp"}
    submit_args_defaults = {}
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
        submit_args_defaults = {k.upper(): v for k, v in new.items()}

    return options, submit_args_defaults
