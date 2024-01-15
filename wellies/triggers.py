"""A collection of reusable families.
"""

import datetime as dt

import pyflow as pf


class OnceAMonthFamily(pf.Family):
    """
    A family whose tasks are only run once a month while
    another/superior YMD is daily.

    Parameters
    ----------
    name : str
        Family name.
    start : datetime | None
        First date to calculate first occurrence from, today if None (default).
    day_of_month : int
        Day of the month. Negative values are relative to 1st of month,
        i.e. -1 is last day of month.
    ymd : pf.Variable | None
        Other YMD to track, by default uses the superior YMD.
    **kwargs :
        Any arguments passed to the family.
    """

    update_ymd_script = """
        # 1st of next month counting from current ymd + 1 as reference
        d={{day_of_month}}
        ref_ymd=$(date -d "$YMD + 1 day" +%Y%m01)

        if (( $d < 0 )); then
            next_ymd=$(date -d "$ref_ymd + 1 month $d day" +%Y%m%d)
        else
            if (( $(date -d $YMD +%d) >= $d )); then
                ref_ymd=$(date -d "$(date -d $YMD +%Y%m01) + 1 month" +%Y%m01)
            fi
            next_ymd=$(date -d "$ref_ymd + $d day - 1 day" +%Y%m%d)
        fi
        ecflow_client --alter change variable YMD $next_ymd {{family_path}}
        ecflow_client --alter change label next_ymd $next_ymd {{family_path}}
    """

    def __init__(
        self,
        name="once_a_month",
        start=None,
        day_of_month=-1,
        ymd=None,
        **kwargs,
    ):
        sd = start or dt.date.today()
        self.day_of_month = day_of_month
        assert day_of_month != 0, "day_of_month must not be 0."
        # calculate first occurrence
        nxt_month = (day_of_month < 0) or (sd.day > day_of_month)
        first_occ = dt.date(
            sd.year, sd.month + (1 if nxt_month else 0), 1
        ) + dt.timedelta(day_of_month - (1 if day_of_month > 0 else 0))

        kwargs.setdefault("YMD", first_occ.strftime("%Y%m%d"))
        super().__init__(
            name=name, labels={"next_ymd": kwargs["YMD"]}, **kwargs
        )
        self.completes = (ymd or self.superior_ymd) != self.YMD

        # add update task, trigger will be set when family is generated
        with self:
            self._update_ymd_task = self.update_ymd_task()

    @property
    def superior_ymd(self):
        p = self.parent
        while True:
            if hasattr(p, "YMD"):
                return p.YMD
            p = p.parent

    def update_ymd_task(self):
        # run this trivial update task on the ecflow server
        # rather than submit to troika
        job_cmd = "bash %ECF_JOB% > %ECF_JOBOUT%"
        script = [
            pf.TemplateScript(
                self.update_ymd_script,
                family_path=self.fullname,
                day_of_month=self.day_of_month,
            ),
        ]
        return pf.Task(
            f"{self.name}_check_next_occurrence",
            script=script,
            ECF_JOB_CMD=job_cmd,
        )

    def generate_node(self):
        """Before generating node, make sure update_ymd_task is only
        triggered when all other tasks have completed.
        """
        chld = [
            c
            for c in self.executable_children
            if c.name != self._update_ymd_task.name
        ]
        for c in chld:
            self._update_ymd_task.triggers &= c
        return super().generate_node()
