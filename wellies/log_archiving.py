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


class ArchivedRepeatFamily(pf.AnchorFamily):
    def __init__(
        self,
        name: str,
        repeat: dict,
        logs_backup: str = None,
        logs_archive: str = None,
        **kwargs,
    ):
        self.logs_backup = logs_backup or None
        self.logs_archive = logs_archive or None
        self._added_log_tasks = False
        variables = kwargs.pop("variables", {})
        if self.logs_backup:
            variables["LOGS_BACKUP"] = self.logs_backup
        if self.logs_archive:
            if not self.logs_backup:
                raise ValueError(
                    "logs_backup must be provided if logs_archive is provided"
                )
            variables["LOGS_ARCHIVE"] = logs_archive
        exit_hooks = kwargs.pop("exit_hook", [])
        exit_hooks.append(self.exit_hook())
        super().__init__(
            name=name,
            exit_hook=exit_hooks,
            variables=variables,
            **kwargs,
        )

        with self:
            self.repeat_attr = repeat_factory(repeat)
            self._archive_task()
            self._loop_task()

    def exit_hook(self):
        if not self.logs_backup:
            return None
        return textwrap.dedent(
            """
            JOBOUT=%ECF_JOBOUT%
            JOB=%ECF_JOB%
            ECF_OUT=%ECF_OUT%
            ECF_HOME=%ECF_HOME%
            LOGS_BACKUP=%LOGS_BACKUP%

            JOB=$(echo $JOB | sed -e "s:$ECF_HOME:$ECF_OUT:")
            JOBDIR=$(echo ${JOBOUT%%/*})
            BACKUP_DIR=$(echo $JOBDIR | sed -e s:$ECF_OUT:$LOGS_BACKUP:)
            if [[ $BACKUP_DIR != "" ]] && [[ $BACKUP_DIR != $JOBDIR ]]
            then
                mkdir -p $BACKUP_DIR
                cp $JOBOUT $BACKUP_DIR/.
                cp $JOB $BACKUP_DIR/.
            fi
            """
        )

    def _loop_task(self):
        if not self.logs_backup:
            return
        script = textwrap.dedent(
            f"""
            dir=$LOGS_BACKUP/$SUITE/$FAMILY
            dir_old=${{dir}}.${self.repeat_attr.name}
            [[ -d $dir ]] && mv $dir $dir_old
            """
        )
        return pf.Task(
            name="loop_logs",
            script=[script],
        )

    def _archive_task(self):
        if not self.logs_backup:
            return
        script = textwrap.dedent(
            f"""
            dir=$LOGS_BACKUP/$SUITE/$FAMILY
            dir_tar=$LOGS_BACKUP/$SUITE

            if [[ -d $dir_tar ]]; then
                cd $dir_tar

                for log in $(ls -d ${{FAMILY}}.*); do
                    REPEAT_TO_TAR=$(echo $log | awk -F'.' '{{print $NF}}')
                    if [[ $REPEAT_TO_TAR -lt ${self.repeat_attr.name} ]]; then
                        TAR_FILE=${{FAMILY}}_${{REPEAT_TO_TAR}}.tar.gz
                        tar -czvf $TAR_FILE $log
                        chmod 644 $TAR_FILE
                        ecp -p $TAR_FILE ${{LOGS_ARCHIVE}}/$TAR_FILE

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
        Before generating node, we need to set the right triggers to the
        loop_log tasks.
        """
        if not self._added_log_tasks:
            if self.logs_backup:
                trigger = None
                for chld in self.executable_children:
                    if chld.name == "loop_logs":
                        continue
                    if trigger is None:
                        trigger = chld.complete
                    else:
                        trigger = trigger & chld.complete
                with self:
                    self.loop_logs.triggers = trigger
            self._added_log_tasks = True

        return super().generate_node()
