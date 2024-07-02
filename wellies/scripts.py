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

log_exit_hook = """
JOBOUT=%ECF_JOBOUT%
JOB=%ECF_JOB%
ECF_OUT=%ECF_OUT%
ECF_HOME=%ECF_HOME%
BACKUP_ROOT=%LOGS_BACKUP_ROOT%

JOB=$(echo $JOB | sed -e "s:$ECF_HOME:$ECF_OUT:")
JOBDIR=$(echo ${JOBOUT%%/*})
BACKUP_DIR=$(echo $JOBDIR | sed -e s:$ECF_OUT:$BACKUP_ROOT:)
if [[ $BACKUP_DIR != "" ]] && [[ $BACKUP_DIR != $JOBDIR ]]
then
    mkdir -p $BACKUP_DIR
    cp $JOBOUT $BACKUP_DIR/.
    cp $JOB $BACKUP_DIR/.
fi
"""

log_move_old = f"""
dir=$LOGS_BACKUP_ROOT/$SUITE/$FAMILY
dir_old=${{dir}}.${self.repeat_var}
[[ -d $dir ]] && mv $dir $dir_old
"""

log_archive = f"""
dir=$LOGS_BACKUP_ROOT/$SUITE/$FAMILY
dir_tar=$LOGS_BACKUP_ROOT/$SUITE

if [[ -d $dir_tar ]]; then
    cd $dir_tar

    for log in $(ls -d ${{FAMILY}}.*); do
        REPEAT_TO_TAR=$(echo $log | awk -F'.' '{{print $NF}}'')
        if [[ $REPEAT_TO_TAR -lt ${self.repeat_var} ]]; then
            TAR_FILE=${{FAMILY}}_${{REPEAT_TO_TAR}}.tar.gz
            tar -czvf $TAR_FILE $log
            chmod 644 $TAR_FILE
            ecp -p $TAR_FILE ${{ECFS_BACKUP}}/$TAR_FILE

            rm -rf $log
            rm -rf $TAR_FILE
        fi
    done
fi
"""
