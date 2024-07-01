import os

import pyflow as pf

from wellies import mars, parse_yaml_files, scripts


class DeployDataFamily(pf.AnchorFamily):
    def __init__(self, data_store, exec_context={}, **kwargs):
        """Defines "static_data" family contaning all tasks needed to deploy
        all types of datasets defined on a [data.StaticDataStore].

        Parameters
        ----------
        data_store : data.StaticDataStore
            A static data store object, usually created from a dictionary-like
            definition.
        exec_context : dict, optional
            An execution context mapping to configure each task submit
            arguments, by default {}
        """
        super().__init__(name="deploy_data", **kwargs)

        with self:
            has_tasks = False
            for dataset, data in data_store.items():
                has_tasks = True
                pf.Task(
                    name=dataset,
                    submit_arguments=data.options.get(
                        "exec_context", exec_context
                    ),
                    script=data.script,
                    labels={"version": "NA"},
                )
            if not has_tasks:
                self.defstatus = pf.state.complete


def process_file_or_string(entry):
    if entry is not None:
        if isinstance(entry, str):
            if os.path.exists(entry):
                script = pf.FileScript(entry)
            else:
                script = entry
        else:
            script = entry
    else:
        script = ""
    return script


class StaticData:
    def __init__(self, data_dir, name, script, options):
        self.name = name
        self.path = os.path.join(data_dir, name)
        self.options = options
        pre_script = process_file_or_string(options.get("pre_script", None))
        post_script = process_file_or_string(options.get("post_script", None))

        script_list = []
        if pre_script:
            script_list.extend(
                [
                    "# Pre-script",
                    pre_script,
                    "",
                ]
            )

        script_list.extend(
            [
                "# Main script for retrieving data",
                "mkdir -p {}".format(data_dir),
                script,
            ]
        )
        if post_script:
            script_list.extend(
                [
                    "# Post-script",
                    post_script,
                    "",
                ]
            )
        self.script = pf.Script(script_list)


class CustomData(StaticData):
    def __init__(self, data_dir, name, options):
        script = "# Running custom data command"
        super().__init__(data_dir, name, script, options)

class Webdata(StaticData):
    def __init__(self, data_dir, name, options):
        script = "# Running custom data command"
        url = options.get("url")
        md5 = options.get("md5")
        name = options.get("name")
        script = pf.TemplateScript(
                scripts.web_script,
                DIR=data_dir,
                NAME=name,
                TARGET=name,
                URL=url
                )
        options.update({"post_script": "test $(echo {}) == $(md5sum {} | awk '{{print $1}}')".format(md5, name)})
        super().__init__(data_dir, name, script, options)


class RsyncData(StaticData):
    def __init__(self, data_dir, name, options):
        tgt = options["source"]
        files = options.get("files")
        if files is not None:
            if not isinstance(files, list):
                files = [files]
            files = [os.path.join(tgt, f) for f in files]
            tgt = files
        else:
            tgt = [tgt]

        script = pf.TemplateScript(
            scripts.rsync_script,
            DIR=data_dir,
            NAME=name,
            TARGET=tgt,
            RSYNC_OPTIONS=options.get("rsync_options", "-avzpL"),
        )
        super().__init__(data_dir, name, script, options)


class CopyData(StaticData):
    def __init__(self, data_dir, name, options):
        tgt = options["source"]
        files = options.get("files")
        if files is not None:
            if not isinstance(files, list):
                files = [files]
            files = [os.path.join(tgt, f) for f in files]
            tgt = files
        else:
            tgt = [tgt]

        script = pf.TemplateScript(
            scripts.copy_script,
            DIR=data_dir,
            NAME=name,
            TARGET=tgt,
        )
        super().__init__(data_dir, name, script, options)


class GitData(StaticData):
    def __init__(self, data_dir, name, options):
        files = options.get("files")
        if files is None:
            script = pf.TemplateScript(
                scripts.git_script,
                DIR=data_dir,
                NAME=name,
                URL=options["source"],
                BRANCH=options.get("branch"),
            )
        else:
            build_dir = os.path.join(data_dir, "git")
            if not isinstance(files, list):
                files = [files]
            files = [os.path.join(build_dir, name, f) for f in files]
            script = [
                pf.TemplateScript(
                    scripts.git_script,
                    DIR=build_dir,
                    NAME=name,
                    URL=options["source"],
                    BRANCH=options.get("branch"),
                ),
                pf.TemplateScript(
                    scripts.rsync_script,
                    DIR=data_dir,
                    NAME=name,
                    TARGET=files,
                    RSYNC_OPTIONS=options.get("rsync_options", "-avzpL"),
                ),
            ]

        super().__init__(data_dir, name, script, options)


class ECFSData(StaticData):
    def __init__(self, data_dir, name, options):
        tgt = options["source"]

        files = options.get("files")
        if files is not None:
            if not isinstance(files, list):
                files = [files]
            files = [os.path.join(tgt, f) for f in files]
            tgt = files
        else:
            tgt = [tgt]

        script = pf.TemplateScript(
            scripts.ecfs_script,
            DIR=data_dir,
            NAME=name,
            TARGET=tgt,
        )
        super().__init__(data_dir, name, script, options)


class LinkData(StaticData):
    def __init__(self, data_dir, name, options):
        script = pf.TemplateScript(
            scripts.link_script,
            DIR=data_dir,
            NAME=name,
            TARGET=options["source"],
        )
        super().__init__(data_dir, name, script, options)


class MarsData(StaticData):
    def __init__(self, data_dir, name, options):
        command = options.get("mars_command", "mars")
        script = [
            f"dest_dir={os.path.join(data_dir, name)}",
            "mkdir -p $dest_dir",
            "cd $dest_dir",
            mars.Retrieve(req=options["request"], command=command),
        ]
        super().__init__(data_dir, name, script, options)


def parse_static_data_item(data_dir, name, options):
    type = options["type"]
    if type == "rsync":
        data = RsyncData(data_dir, name, options)
    elif type == "copy":
        data = CopyData(data_dir, name, options)
    elif type == "git":
        data = GitData(data_dir, name, options)
    elif type == "web":
        data = Webdata(data_dir, name, options)
    elif type == "ecfs":
        data = ECFSData(data_dir, name, options)
    elif type == "link":
        data = LinkData(data_dir, name, options)
    elif type == "mars":
        data = MarsData(data_dir, name, options)
    elif type == "custom":
        data = CustomData(data_dir, name, options)
    else:
        raise Exception(f"Static data type {type} not supported")
    return data


class StaticDataStore:
    def __init__(self, data_dir: str, static_data_dict: dict):
        """
        The StaticDataStore contains a set of static data items and their
        associated scripts to be used to deploy the items when running the
        suite.

        Parameters
        ----------
        data_dir (str):
            The directory where the data is stored on the running host.
        static_data_dict (dict):
            A dictionary containing the names of the static data items as
            keys and their deployment options as values.
        """
        self.static_data = {}
        for name, options in static_data_dict.items():
            data = parse_static_data_item(data_dir, name, options)
            self.static_data[name] = data

    def __getitem__(self, item):
        return self.static_data[item]

    def __repr__(self) -> str:
        items = str({name: it.options for name, it in self.items()})
        return f"StaticDataStore: {items}"

    def items(self):
        return self.static_data.items()

    @classmethod
    def from_yamls(cls, config_files: list, data_dir=None):
        options = parse_yaml_files(config_files)
        if data_dir is None:
            rootname = "$DATA_DIR"
        else:
            if data_dir in options:
                rootname = options[data_dir]
            else:
                rootname = data_dir
        cls(rootname, options["static_data"])
