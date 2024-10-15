/// admonition | Page Under Construction
    type: Warning
///

# Building a suite from scratch

## A default suite

In this guide we will go through the steps of creating a suite from the very beginning.
This suite will be named `efas_report` and its code will live in a directory named 
`projects`.

```shell
$ wellies-quickstart -p efas_report ~/projects/efas_report
$ cd ~/projects/efas_report
```

The command will start the project with associated base configuration files in the target directory.
Before we do any further changes, it's always good to keep track of our changes. So, let's initialize a local git repository

```console
$ git init
$ echo "__pycache__" > .gitignore
$ git add --all
$ git commit -m "Start of project from wellies-quickstart"
```

This example suite is ready to deploy and we can do this by running

```console
$ ./deploy configs/*.yaml
running on host: localhost
------------------------------------------------------
Staging suite to /tmp/build_efas_report_8smyc2z4
------------------------------------------------------
Generating suite:
    -> Deploying suite scripts in /tmp/build_efas_report_8smyc2z4/staging
    -> Definition file written in /tmp/build_efas_report_8smyc2z4/staging/efas_report.def
Creating deployer:
    -> Loading local repo /tmp/build_efas_report_8smyc2z4/local
    -> Cloning from /perm/username/pyflow/efas_report

Remote repository does not seem to exist. Do you want to initialise it? (N/y) y

Creating remote repository /perm/username/pyflow/efas_report on host localhost with user username
Creating deployer:
    -> Loading local repo /tmp/build_efas_report_8smyc2z4/local
    -> Cloning from /perm/username/pyflow/efas_report
Changes in staged suite:
    - Removed:
        - dummy.txt
    - Added:
        - efas_report.def
        - init/deploy_tools/deploy_tools.man
        - init/deploy_tools/suite_env/setup.ecf
        - init/deploy_tools/suite_env/earthkit.ecf
        - init/deploy_tools/suite_env/packages.man
        - init/deploy_data/git_sample.ecf
        - init/deploy_data/mars_sample.ecf
        - main/dummy.ecf
For more details, compare the following folders:
/tmp/build_efas_report_8smyc2z4/staging
/tmp/build_efas_report_8smyc2z4/local
------------------------------------------------------
Deploying suite to /perm/username/pyflow/efas_report
------------------------------------------------------

You are about to push the staged suite to the target directory. Are you sure? (N/y)y
Deploying suite to remote locations
    -> Checking that git repos are in sync
    -> Staging suite
    -> Git commit
    -> Git push to target /perm/username/pyflow/efas_report on host localhost
Suite deployed to /perm/username/pyflow/efas_report
Definition file: /perm/username/pyflow/efas_report/efas_report.def
```

This script has:

1. Read the configuration files
2. Created suite files in the `/tmp/build_efas_report_8smyc2z4/staging` folder
3. Created a git repository in `/perm/username/pyflow/efas_report`, our git remote
4. Cloned that repository to `/tmp/build_efas_report_8smyc2z4/local`
5. Updated the suite, committed the changes and pushed to `/perm/username/pyflow/efas_report`

> [!NOTE]  
> Paths to the temporary directories have been changed for brevity

We've deployed the default suite, now let's look at how we can configure it to do what we want.

## Customisation

When we ran the deploy script we passed it the path to the configuration files `configs/*.yaml`.
Within that directory there are four files

```tree
configs/
    config.yaml
    data.yaml
    execution_contexts.yaml
    tools.yaml
```

Let's first take a look at `config.yaml`

### `config.yaml`

```yaml title="config.yaml"
# Configuration file for pyflow suite.

# This file only contains a selection of most common options.
# All new entries can be treated on /etc/ecmwf/nfs/dh1_home_a/username/projects/efas_report/suite/config.py:Config

# wellies support simple python string formatting and have some global names available.
# This will be treated accordingly by wellies.parse_yaml:

# name: mysuite
# suite_dir: "{HOME}/{name}"

# Available names are:
# USER, HOME, PERM, SCRATCH, PWD, HPCPERM, TODAY and YESTERDAY

# -------- Suite deployment configuration -------------------------------------
# host options
suite_name: "efas_report"
hostname: "localhost"
user: "{USER}"

# server options
deploy_dir: "{PERM}/pyflow/efas_report"
job_out: "%ECF_HOME%"
workdir: "$TMPDIR"

output_root: "{SCRATCH}/efas_report"

# ---------- Specific optionals -----------------------------------------------
# add your project's specific variables and options here
```

Let's break down the configuration settings.

#### Host options

- `suite_name` - the name of the suite
- `hostname` - the host on which we want the suite to run, such as our HPC cluster
- `user` - by default `{USER}` will be replaced with our username, it should be set to your username on the HPC system running the suite

#### Server options

- `deploy_dir` - where the main suite files and git repo will be created, `/perm/username/pyflow/efas_report` above
- `job_out` - job output directory, where files should be created
- `workdir` - a temporary working directory read/write purposes
- `output_root` - a folderpath used for storage of tools, Python environments and static data stores

Let's update the configuration to use a new host and username

```yaml
# host options
suite_name: "efas_report"
hostname: "hpc_system.example.com"
user: "myusername"

# server options
deploy_dir: "{PERM}/pyflow/efas_report"
job_out: "%ECF_HOME%"
workdir: "$TMPDIR"

output_root: "{SCRATCH}/efas_report"
```

To deploy the suite again we do

```console
$ ./deploy configs/*.yaml
submitting jobs using troika on host: hpc_system.example.com
------------------------------------------------------
Staging suite to /tmp/build_efas_report_eheea31w
------------------------------------------------------
Generating suite:
    -> Deploying suite scripts in /tmp/build_efas_report_eheea31w/staging
    -> Definition file written in /tmp/build_efas_report_eheea31w/staging/efas_report.def
Creating deployer:
    -> Loading local repo /tmp/build_efas_report_eheea31w/local
    -> Cloning from /perm/username/pyflow/efas_report
Changes in staged suite:
    - Modified:
        - efas_report.def
        - init/deploy_data/git_sample.ecf
        - init/deploy_data/mars_sample.ecf
        - init/deploy_tools/suite_env/earthkit.ecf
        - init/deploy_tools/suite_env/setup.ecf
        - main/dummy.ecf
For more details, compare the following folders:
/tmp/build_efas_report_eheea31w/staging
/tmp/build_efas_report_eheea31w/local
------------------------------------------------------
Deploying suite to /perm/username/pyflow/efas_report
------------------------------------------------------
You are about to push the staged suite to the target directory. Are you sure? (N/y)y
Deploying suite to remote locations
    -> Checking that git repos are in sync
    -> Staging suite
    -> Git commit
    -> Git push to target /perm/username/pyflow/efas_report on host localhost
Suite deployed to /perm/username/pyflow/efas_report
Definition file: /perm/username/pyflow/efas_report/efas_report.def
```

With this deployment wellies detects that changes have been made to the configuration file, updates the suite and informs us the changes will be committed and pushed to the deployment directory.

You may notice on at the top of the wellies output the line `submitting jobs using troika on host: hpc_system.example.com`, this tells 
us [troika](https://github.com/ecmwf/troika) will be used to deploy the tasks for this suite. We'll cover different hosts in a later tutorial or you can here more in the [execution contexts](./config/exec_config.md) documentation.

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
attribute poiting to a `ToolStore` object.

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