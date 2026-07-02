from importlib.resources import files
import pyflow

class ScriptLoader:
    """Simple class to load sample scripts and snippets from the wellies/scripts directory as 
    package resources.

    The main method `.load` takes a script name and returns the contents of the script as a list of lines.
    """

    def __init__(self, subdir: str = "scripts"):
        self.subdir = subdir

    def load(self, script_name: str) -> pyflow.Script:
        """Load a script from the wellies/scripts directory.

        Args:
        -----
            script_name (str): The name of the script to load.
        Returns:
        --------
            pyflow.Script: The contents of the script as a pyflow.Script object.
        """
        resource = files("wellies")
        for part in self.subdir.split("/"):
            resource = resource.joinpath(part)
        return pyflow.Script(resource.joinpath(script_name).read_text().splitlines())


# flake8: noqa
def update_label(label, value):
    return "ecflow_client --label={} {}".format(label, value)


def update_label_version():
    return update_label(
        "version",
        "$(if [[ -f version.txt ]]; then cat version.txt; else echo NA; fi)",
    )


git_script = """
dest_dir={{ DIR }}/{{ NAME }}
rm -rf $dest_dir
giturl={{ URL }}
gitbranch={{ BRANCH }}
git clone $giturl --branch $gitbranch --single-branch --depth 1 $dest_dir
cd $dest_dir

"""

rsync_script = """
dest_dir={{ DIR }}/{{ NAME }}
rsync {{ RSYNC_OPTIONS }} {% for item in TARGET %}{{ item }} {% endfor %} $dest_dir/
cd $dest_dir

"""

copy_script = """
dest_dir={{ DIR }}/{{ NAME }}
rm -rf $dest_dir
mkdir -p $dest_dir
scp {% for item in TARGET %}{{ item }} {% endfor %} $dest_dir/
cd $dest_dir

"""

ecfs_script = """
dest_dir={{ DIR }}/{{ NAME }}
rm -rf $dest_dir
mkdir -p $dest_dir
ecp {% for item in TARGET %}{{ item }} {% endfor %} $dest_dir/
cd $dest_dir

"""

link_script = """
dest_dir={{ DIR }}/{{ NAME }}
rm -rf $dest_dir
ln -sfn {{ TARGET }} $dest_dir
if [[ -L $dest_dir && -d $(readlink $dest_dir) ]]; then
    echo Link and directory exist
else
    echo Link or directory does not exist
    exit 1
fi
cd $dest_dir

"""

set_clear_event = """ecflow_client --alter change event {{ EVENT }} {{ ACTION }} {{ SUITE_PATH }}
"""
