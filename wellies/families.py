import textwrap

import pyflow as pf


def repeat_factory(options):
    if options["type"] == "RepeatDate":
        return pf.RepeatDate(
            options["name"],
            options["begin"],
            options["end"],
            options.get("step", 1),
        )
    else:
        raise ValueError(f"Unknown repeat type: {options['type']}")


class ArchivedRepeatFamily(pf.Family):

    def __init__(
        self,
        name: str,
        repeat: dict,
        backup_root: str = None,
        ecfs_backup: str = None,
    ):
        self.backup_root = backup_root or None
        self.repeat_var = repeat["name"]
        self._added_log_tasks = False
        variables = {}
        if self.backup_root:
            if not ecfs_backup:
                raise ValueError(
                    "ecfs_backup must be provided if backup_root is provided"
                )
            variables["LOGS_BACKUP_ROOT"] = self.backup_root
            variables["ECFS_BACKUP"] = ecfs_backup
        super().__init__(
            name=name,
            exit_hook=self.exit_hook(),
            variables=variables,
        )

        with self:
            repeat_factory(repeat)

    def exit_hook(self):
        if not self.backup_root:
            return None
        return textwrap.dedent(
            """
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
        )

    def _loop_task(self):
        script = textwrap.dedent(
            f"""
            dir=$LOGS_BACKUP_ROOT/$SUITE/$FAMILY
            dir_old=${{dir}}.${self.repeat_var}
            [[ -d $dir ]] && mv $dir $dir_old
            """
        )
        return pf.Task(
            name="loop_logs",
            script=[script],
        )

    def _archive_task(self):
        script = textwrap.dedent(
            f"""
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
        )
        return pf.Task(
            name="archive_logs",
            script=[script],
        )

    def generate_node(self):
        """
        Before generating node, we need to add the log archiving
        tasks.
        """
        if not self._added_log_tasks:
            if self.backup_root:
                trigger = None
                for chld in self.executable_children:
                    if trigger is None:
                        trigger = chld.complete
                    else:
                        trigger = trigger & chld.complete
                with self:
                    archive = self._archive_task()
                    loop = self._loop_task()
                    loop.triggers = trigger & archive.complete
            self._added_log_tasks = True

        return super().generate_node()
