/// admonition | Page Under Construction
    type: Warning
///

# Building a suite from scratch

In this guide we will go through the steps of creating a suite from the very beginning.
This suite will be named `efas_report` and its code will live in a directory named 
`projects`.

```shell
$ wellies-quickstart -p efas_report ~/projects/efas_report
$ cd ~/projects/efas_report
```

The command will start the project with associated base configuration files in the target directory.

Before we do any further changes, it's always good to keep track of our changes. So, let's initialize a local git repository

```shell
$ git init
$ echo "__pycache__" > .gitignore
$ git add --all
$ git commit -m "Start of project from wellies-quickstart"
```

We can already deploy this suite by running.

```shell
$ ./deploy configs/*.yaml
```

You will notice that this suite comes already powered with git-tracked deployment provided by [tracksuite](tracksuite_guide.md). We can accept all the prompts and have the suite definition and its scripts deployed to `deploy_dir`, as defined in the main configuration file, `configs/config.yaml`.

We want to run our suite on a remote hpc cluster accessible via ssh with name `hpc`. We 
can define that with the `hostname` option in `configs/config.yaml` to the desired name.

If we try to deploy again we will see that all files have been modified. Is that alright!? If we take the advice from 
the prompt and call a `diff` command on the script `init/deploy_data/mars_sample.ecf` we will see that some headers have been added now that we are setting up to run on a different execution host.

/// admonition | Note
    type: Hint
In the [execution configuration](config/exec_config) there is extra information about how the Host type and the Task share some features about the execution context and how one can leverage that.
///

Other entries of the main configuration file look good for the moment and we are leaving them as they are for now.

In our workflow we will need two datasets that are *static*, or they are data that need to be fetched just once for our computations to work. So, within the `configs/data.yaml` we will add entries to transfer the latest station file from EFAS repository and the computed flood thresholds that we know are available in a shared directory. 

The EFAS station file is tracked within EFAS suite repository, so we are fetching it from there and from the latest version from the `develop` branch. We don't want to keep the whole repository as we are just interested in this specific file and therefore can use the `files` option to narrow it down.
The thresholds and upstream area are simple files that we will be accessing from a shared space.

The new `static_data` entry should look like this.

```yaml title="data.yaml"
static_data:
    outlets:
        type: git
        source: git@git.server.com:myproject/repo.git
        branch: develop
        files: ["repodata/stations.csv"]
    static_maps:
        type: copy
        source: "/path/to/shared/directory"
        files:
        - "thresholds.nc"
        - "upstream_area.nc"
```

We will notice that the `deploy_data` family and scripts were modified. 
By loading our suite on an running ecflow_server we can start running some jobs.

The first step of our main computation will involve plotting **EFAS forecast** for 
the available forecast within a **date range** and for each of the existing **two** 
model runs. In our example we can add configuration options accordingly:

```yaml title="configs/config.yaml"
n_cycles: 2
start_date: 202401-01
end_date: 202401-07
```

And for the retrieval we can use wellies to configure our MARS request. We want 
a netcdf output and for that we call the `grib_to_netcdf` command line tool. 
Back to `data.yaml` we can define a custom data type of mars request as:

```yaml title="configs/data.yaml"
forecasts:
    - name: eud
      type: mars
      request:
        class: ce
        stream: efas
        expver: 1
        model: lisflood
        levtype: sfc
        origin: ecmf
        type: fc
        param: 240023
        step: 6/to/240/by/6
        target: dis.grb
        time: ${HH}:00:00
        date: $YMD
      post_script: 'grib_to_netcdf -o dis.nc dis.grb'
    - name: dwd
      type: mars
      request:
        class: ce
        stream: efas
        expver: 1
        model: lisflood
        levtype: sfc
        origin: edzw
        type: fc
        param: 240023
        step: 6/to/168/by/6
        target: dis.grb
        time: ${HH}:00:00
        date: $YMD
      post_script: 'grib_to_netcdf -o dis.nc dis.grb'
```

And that will be read in the `Config` object in `deploy.py` where we use wellies 
data parser:

```python title="suite/nodes.py"
# class Config:__init__
from datetime import datetime as dt
# (...)

    self.cycles = range(0, 24, 24 // options.get('n_cycles', 1))
    self.start_date = dt.strptime(options['start_date'], "%Y%m-%d")
    self.end_date = dt.strptime(options['start_date'], "%Y%m-%d")

    self.fc_retrievals = [
        wl.data.parse_static_data_item("$OUTPUT_ROOT", entry['name'], entry)
            for entry in options.get('forecasts', {})
    ]
```

So, to add such node in our suite we will modify the main family definition at the 
file `suite/nodes.py` where we have the `MainFamily` definition with a single 
placeholder task in it. Let's replace this by a repeating node that will run 
every day, retrieve the input data for each cycle and then run our processing. We see 
that the `MainFamily` class receives a config argument so we can use that to carry 
on data like, start and end dates and the keys for our data retrieval.

For readability we can define a `IssueFamily` class that holds the logic of a 
single run of our analysis and transfer the configuration of how many cycles we 
are going to run.

The `post_script` added to our retrievals, runs an external conversion tool 
provided by the `ecmwf-toolbox` module. We need to add such runtime dependency on top of 
our script. The way to do it is again via the `config` object which has a `tools` 
attribute pointing to a `ToolStore` object.

```python title="suite/nodes.py"
class IssueFamily(pf.Family):
    def __init__(self, config, hh, **kwargs):
        hh_label = f"{hh:02.0f}"
        variables = kwargs.pop('variables', {})
        variables.update(dict(HH=hh_label))
        super().__init__(name=hh_label, variables=variables, **kwargs)
        with self:
            # retrieve data
            n_ret = pf.Task(
                name='retrieve',
                script=[
                    config.tools.load('ecmwf-toolbox'),
                    [dd.script for dd in config.fc_retrievals],
                ],
            )
            # run report
            n_plt = pf.Task(name='plots')
        n_plt.triggers = n_ret.complete


class MainFamily(pf.AnchorFamily):
    def __init__(self, config, **kwargs):
        super().__init__(name='main', **kwargs)
        with self:
            pf.RepeatDate(name='YMD', start=config.start_date, end=config.end_date)
            f_previous = None
            for cycle in config.cycles:
                f_issue = IssueFamily(config, cycle)
                if f_previous is not None:
                    f_issue.triggers = f_previous.complete
                    f_previous = f_issue
```



# TODO's
show jupyter notebook that run earthkit maps plotting for efas data. Create script that runs with arguments appropriate


## defined variables

lib_dir
data_dir