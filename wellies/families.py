import pyflow as pf
from wellies import scripts


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
        return scripts.log_exit_hook

    def _loop_task(self):
        return pf.Task(
            name="loop_logs",
            script=[scripts.log_move_old],
        )

    def _archive_task(self):
        return pf.Task(
            name="archive_logs",
            script=[scripts.log_archive],
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
