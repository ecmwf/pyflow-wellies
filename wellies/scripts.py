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
