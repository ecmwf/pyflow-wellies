# Building a suite

## A default suite

This tutorial will cover creating a wellies suite, from the creation of the default configuration files to the customisation
and deployment of the suite. We'll use the `wellies-quickstart` tool to create all of the files and folders we need to build a wellies suite.

We'll start by creating a new project called `efas-report` in the current directory. For advanced options, see the help using `-h`.

```shell
$ wellies-quickstart efas-report
```

Let's have a look at the folder created

```tree
efas-report/
├── build.sh
├── configs
│   ├── data.yaml
│   ├── host.yaml
│   ├── tools.yaml
│   └── user.yaml
├── deploy.py
└── efas_report
    └── __init__.py
    └── config.py
    └── nodes.py
├── profiles.yaml
└── tests
    └── test_configs.py
```

We can see that suite configuration files, a profiles file, a deployment Python script, a build shell script, a tests folder and suite customisation code have been created for us. Before we start we'll initialise a git repository so we can keep track of our changes.

```shell
$ cd efas-report
$ git init
$ echo "__pycache__" > .gitignore
$ git add --all
$ git commit -m "Start of project from wellies-quickstart"
```

The example suite is ready to deploy and we can do this using `build.sh` and passing it the profile name we want to deploy.

```shell
$ ./build.sh user
Running on host: localhost
------------------------------------------------------
Staging suite to /tmp/build_efas_report_9xfrl_pw
------------------------------------------------------
Generating suite:
    -> Deploying suite scripts in /tmp/build_efas_report_9xfrl_pw/staging
    -> Definition file written in /tmp/build_efas_report_9xfrl_pw/staging/efas_report.def
Creating deployer:
    -> Loading local repo /tmp/build_efas_report_9xfrl_pw/local
    -> Cloning from /perm/username/pyflow/efas_report
Remote repository does not seem to exist. Do you want to initialise it? (N/y)y
Creating remote repository /perm/username/pyflow/efas_report on host localhost with user username
Creating deployer:
    -> Loading local repo /tmp/build_efas_report_9xfrl_pw/local
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
/tmp/build_efas_report_9xfrl_pw/staging
/tmp/build_efas_report_9xfrl_pw/local
------------------------------------------------------
Deploying suite to /perm/username/pyflow/efas_report
------------------------------------------------------
You are about to push the staged suite to the target directory. Are you sure? (N/y)y
Could not find local git repository, using default message
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
2. Created suite files in the `/tmp/build_efas_report_9xfrl_pw/staging` folder
3. Created a git repository in `/perm/username/pyflow/efas_report`, our git remote
4. Cloned that repository to `/tmp/build_efas_report_9xfrl_pw/local`
5. Updated the suite, committed the changes and pushed to `/perm/username/pyflow/efas_report`

/// admonition | Note
    type: Hint
Paths to the temporary directories have been changed for brevity
///

We've deployed the default suite, now let's look at how we can configure it to do what we want.

### Deploying the suite

We can deploy this default suite to an ecflow server using `ecflow_client`.
You'll need to either load the `ecflow` module or [install ecflow](https://ecflow.readthedocs.io/en/latest/install/index.html).

```console
$ ecflow_client --host ecflow_server.example.com --port 3141 --load /perm/username/pyflow/efas_report/efas_report.def
```

## Customising the suite

When we ran the deploy script we passed it the `user` profile. This refers to one of the profiles defined in the `profiles.yaml` file.
This file contains the deployment profiles (typically test, operation, dev, etc.) available for the suite. The quickstart gives the following:
```yaml
# This file contains the main configuration profiles
user:
  - configs/user.yaml
  - configs/host.yaml
  - configs/data.yaml
  - configs/tools.yaml
```

We can see that the file contains one profile `user`, pointing to some configuration files located in the `configs` directory.
For a quick overview of what these files do:

- `config.yaml` - handles the [pyflow](https://github.com/ecmwf/pyflow) suite, repository and ecflow server config
- [`data.yaml`](./config/data_config.md) - configuration of data retrieval and handling
- [`host.yaml`](./config/host.md) - for configuring how tasks are executed on hosts and queueing systems such as SLURM
- [`tools.yaml`](./config/tools_config.md) - for conda environment creation and loading, environment variable handling etc


Click on filenames above for more information on available configuration options.

To start, let's take a look at `user.yaml`

### `user.yaml`

This file handles the configuration of the [pyflow](https://github.com/ecmwf/pyflow) suite and repository
in which the suite is stored. We'll start with the minimal example generated by wellies.

```yaml title="config.yaml"
# Configuration file for pyflow suite.

# This file only contains a selection of most common options.
# All new entries can be treated on {{ project_root }}/suite/config.py:Config

# wellies support simple python string formatting and have some global names available.
# This will be treated accordingly by wellies.parse_yaml:

# name: mysuite
# suite_dir: "{HOME}/{name}"

# Available names are:
# USER, HOME, PERM, SCRATCH, PWD, HPCPERM, TODAY and YESTERDAY

# -------- Suite deployment configuration -------------------------------------
name: "efas_report"

ecflow_server:
  hostname: "localhost"
  user: "{USER}"
  deploy_dir: "{PERM}/pyflow/efas_report"

# -------- Global variables ------------------------------------
ecflow_variables:
  OUTPUT_ROOT: "{SCRATCH}"
  LIB_DIR: "%OUTPUT_ROOT%/local"
  DATA_DIR: "%OUTPUT_ROOT%/data"

# ---------- Specific optionals -----------------------------------------------
# add your project's specific variables and options here

```

To break down the configuration settings:

- `name` - the name of the suite
- `ecflow_server`
    - `hostname` - hostname of the ecflow server
    - `user` - username to use on the ecflow server
    - `deploy_dir` - directory to deploy suite files on the ecflow server
- `ecflow_variables` - any number of variables that can be used by the ecflow suite, required values are
    - `OUTPUT_ROOT` - suite output root path
    - `LIB_DIR` - directory used for storage of tools, Python environments
    - `DATA_DIR` - used for storage of static data

Let's update the configuration to use a fixed username on the ecflow server

```yaml title="config.yaml"
name: "efas_report"

ecflow_server:
  hostname: "localhost"
  user: "ecflow_username"
  deploy_dir: "{PERM}/pyflow/efas_report"

# -------- Global variables ------------------------------------
ecflow_variables:
  OUTPUT_ROOT: "{SCRATCH}"
  LIB_DIR: "%OUTPUT_ROOT%/local"
  DATA_DIR: "%OUTPUT_ROOT%/data"
```

To deploy the updated suite we do

```shell
$ ./build.sh user
Running on host: localhost
------------------------------------------------------
Staging suite to /tmp/build_efas_report_k52s_1ra
------------------------------------------------------
Generating suite:
    -> Deploying suite scripts in /tmp/build_efas_report_k52s_1ra/staging
    -> Definition file written in /tmp/build_efas_report_k52s_1ra/staging/efas_report.def
Creating deployer:
    -> Loading local repo /tmp/build_efas_report_k52s_1ra/local
    -> Cloning from /perm/username/pyflow/efas_report
Changes in staged suite:
    - Modified:
        - efas_report.def
For more details, compare the following folders:
/tmp/build_efas_report_k52s_1ra/staging
/tmp/build_efas_report_k52s_1ra/local
------------------------------------------------------
Deploying suite to /perm/username/pyflow/efas_report
------------------------------------------------------
You are about to push the staged suite to the target directory. Are you sure? (N/y)y
Could not find local git repository, using default message
Deploying suite to remote locations
    -> Checking that git repos are in sync
    -> Staging suite
    -> Git commit
    -> Git push to target /perm/username/pyflow/efas_report on host localhost
Suite deployed to /perm/username/pyflow/efas_report
Definition file: /perm/username/pyflow/efas_report/efas_report.def
```

With this deployment wellies detects that changes have been made to the configuration file, updates the suite and informs us the changes will be committed and pushed to the deployment directory.

### `data.yaml`

This file configures data retrieval and handling. In our workflow we will need two datasets that are *static*, or they are data that need to be fetched just once for our computations to work. Within `configs/data.yaml` we will add entries to transfer the latest station file from the EFAS repository and the computed flood thresholds that we know are available in a shared directory.

We'll start by creating an `outlets` section in our `configs/data.yaml` file.
The EFAS station file is tracked within EFAS suite repository, we tell wellies to clone the repo, use the `develop` branch and just keep the files specified in the `files` list. Next we add a `static_maps` section for the thresholds and upstream area files.

```yaml title="data.yaml"
static_data:
    outlets:
        type: git
        source: https://github.com/myproject/repo.git
        branch: develop
        files: ["repodata/stations.csv"]
    static_maps:
        type: copy
        source: "/path/to/shared/directory"
        files:
        - "thresholds.nc"
        - "upstream_area.nc"
```

For more information on the options available see the [static data documentation](./config/data_config.md).

### Expanding the suite

We want our suite to do something with the datasets, to add extra tasks to our suite we go back to the `config.yaml`.
The first step of our main computation will involve plotting **EFAS forecast** for
the available forecast within a **date range** and for each of the existing **two**
model runs. In our example we can add configuration options accordingly:

```yaml title="config.yaml"
n_cycles: 2
start_date: "20240101"
end_date: "20240107"
```

Next we use wellies to configure a MARS request. We give each request a name, a type, here `mars` and a request body.
The `post_script` keyword allows us to run a tool on the result of the request. We want a netCDF instead of GRIB so we call the `grib_to_netcdf` command line tool provided by the `ecmwf-toolbox` module.

Here we modify `data.yaml` to add those changes:

```yaml title="data.yaml"
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
        target: dis_eud.grb
        time: ${HH}:00:00
        date: $YMD
      post_script: 'grib_to_netcdf -o dis_eud.nc dis_eud.grb'
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
        target: dis_dwd.grb
        time: ${HH}:00:00
        date: $YMD
      post_script: 'grib_to_netcdf -o dis_dwd.nc dis_dwd.grb'
```

This is a good place to pause so we can better understand how wellies parses these configuration files.

When we run the deploy command

```console
$ ./build.sh user
```

wellies reads and parses the YAML files defined in the profile. The configuration settings are stored in a `Config` object created from the class that's defined in `config.py`.

```python title="config.py"
class Config:
    # Configuration templates global variables
    global_vars = {
        "ROOT": ROOT_DIR,
        "NAME": os.path.splitext(os.path.basename(__file__))[0],
    }

    def __init__(self, args):

        # Parse the configuration files
        options = wl.parse_profiles(
            args.profiles,
            config_name=args.name,
            set_variables=args.set,
            global_vars=self.global_vars,
        )

        # put everything from the yaml into class variables
        self.__dict__.update(options)

        # Ecflow server options
        self.ecflow_server = wl.EcflowServer(**options["ecflow_server"])
        ...
```

We can modify this class to allow us to pass in new configuration options.
We want to pass the number of cycles, the start date and the end date. Let's update the class to take these values.

```python title="config.py"
from datetime import datetime as dt

class Config:
    # Configuration templates global variables
    global_vars = {
        "ROOT": ROOT_DIR,
        "NAME": os.path.splitext(os.path.basename(__file__))[0],
    }

    def __init__(self, args):

        # Parse the configuration files
        options = wl.parse_profiles(
            args.profiles,
            config_name=args.name,
            set_variables=args.set,
            global_vars=self.global_vars,
        )

        # put everything from the yaml into class variables
        self.__dict__.update(options)

        # Ecflow server options
        self.ecflow_server = wl.EcflowServer(**options["ecflow_server"])

        self.cycles = range(0, 24, 24 // options.get('n_cycles', 1))
        self.start_date = dt.strptime(options['start_date'], "%Y%m%d")
        self.end_date = dt.strptime(options['end_date'], "%Y%m%d")

        self.fc_retrievals = [
            wl.data.parse_data_item("$OUTPUT_ROOT", entry['name'], entry)
            for entry in options.get('forecasts', {})
    ]
```

To add such a node to our suite we will modify the main family definition in `nodes.py`.
At the moment we have the `MainFamily` definition with a single placeholder task in it.


```python title="suite/nodes.py"
class MainFamily(pf.AnchorFamily):
    def __init__(self, config, **kwargs):
        super().__init__(name='main', **kwargs)
        with self:
            pf.Task(
                name='dummy',
            )
```

Let's replace this by a repeating node that will run
every day, retrieve the input data for each cycle and then run our processing. We see
that the `MainFamily` class receives a config argument so we can use that to pass data such as
start and end dates and the keys for our data retrieval.

```python title="nodes.py"
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

For readability we also define an `IssueFamily` class that holds the logic of a
single run of our analysis and configures how many cycles we are going to run.

The `post_script` added to our retrievals in `data.yaml` uses an external conversion tool
provided by the `ecmwf-toolbox` module. We need to let wellies know we're going to use this module by making sure it's in our `tools.yaml` file.

```yaml title="tools.yaml"
tools:
  modules:
    python:
      name: python3
      version: 3.12.9-01
    ecmwf-toolbox:
      version: 2024.09.0.0
      depends: [python]
  packages:
    scripts:
      type: rsync
      source: "{ROOT}/scripts"
  environments:
      suite_env:
          type: system_venv
          depends: [python, ecmwf-toolbox]
          packages: [scripts]
```

We're now able to add the loading of the `ecmwf-toolbox` module to our script using the `config.tools.load('ecmwf-toolbox')`
call.

```python
n_ret = pf.Task(
            name='retrieve',
            script=[
                config.tools.load('ecmwf-toolbox'),
                [dd.script for dd in config.fc_retrievals],
            ],
        )
```  

For more detail on using tools see the [tools documentation](./config/tools_config.md).

We've now defined most of the components of the suite. The remaining piece
is the actual plotting task that produces our EFAS-style report maps.

## Creating the plotting script

Our `plots` task needs a script that reads the retrieved GRIB data and produces
a map for each forecast step. We'll create a Python script based on
[earthkit-plots](https://earthkit-plots.readthedocs.io/en/stable/examples/gallery/gridded-data/efas.html)
and wrap it in a bash launcher that the ecflow task will call.

First, create the plotting script in your project's `efas_report/scripts/` directory:

```python title="efas_report/scripts/plot_efas.py"
"""Produce an EFAS-style discharge map for a single forecast step."""
import sys
from pathlib import Path

import earthkit.data
import earthkit.plots

def plot_step(input_file, output_dir, step):
    """Plot a single forecast step and save as PNG."""
    ds = earthkit.data.from_source("file", input_file)
    field = ds.sel(step=step)

    chart = earthkit.plots.Map()
    chart.plot(field)
    chart.title(f"EFAS Report - T+{step}h")

    output_path = Path(output_dir) / f"efas_step_{step:03d}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    chart.save(str(output_path))
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    plot_step(
        input_file=sys.argv[1],
        output_dir=sys.argv[2],
        step=int(sys.argv[3]),
    )
```

Then create the bash wrapper that ecflow will execute. This iterates over
forecast steps for the current date and cycle:

```bash title="efas_report/scripts/run_plots.sh"
#!/bin/bash
# Run plotting for all forecast steps
# Variables YMD, HH, STEPS are provided by ecflow

INPUT_DIR="$OUTPUT_ROOT/data/$YMD/$HH"
OUTPUT_DIR="$OUTPUT_ROOT/plots/$YMD/$HH"

for STEP in $STEPS; do
    INPUT_FILE="$INPUT_DIR/forecast_step_${STEP}.grib"
    python $LIB_DIR/scripts/plot_efas.py "$INPUT_FILE" "$OUTPUT_DIR" "$STEP"
done

echo "All plots complete for $YMD cycle $HH"
```

## Wiring the script into the suite

Now we update the `plots` task in our `IssueFamily` to execute the wrapper
script, loading the required tools environment first:

```python title="nodes.py"
class IssueFamily(pf.Family):
    def __init__(self, config, hh, **kwargs):
        hh_label = f"{hh:02.0f}"
        variables = kwargs.pop('variables', {})
        variables.update(dict(HH=hh_label, STEPS="6 12 18 24 48 72"))
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
            n_plt = pf.Task(
                name='plots',
                script=[
                    config.tools.load('suite_env'),
                    "bash $LIB_DIR/scripts/run_plots.sh",
                ],
            )
        n_plt.triggers = n_ret.complete
```

The `scripts/` directory needs to be declared in `tools.yaml` as a package so
it gets deployed alongside the suite (already done in our earlier configuration).

## Deploying and running the suite

With all components in place, deploy the suite using the build script:

```shell
$ ./build.sh user
```

This will:

1. Parse the `user` profile (defined in `profiles.yaml`) to load all config files.
2. Generate the ecflow suite definition including all tasks, triggers, and scripts.
3. Deploy scripts and definitions to the configured output directories.

To generate the suite without deploying (useful for local inspection):

```shell
$ ./build.sh user -n
```

/// admonition | Tip
    type: tip
Use `-y` to skip interactive confirmation prompts during deployment, e.g.
`./build.sh user -y`.
///

## Testing locally

The generated project includes a test suite that validates your configuration
builds correctly:

```shell
$ ./build.sh tests
```

This runs pytest against your suite definitions, ensuring all profiles produce
valid ecflow definitions without needing access to the actual server.

## Summary

In this tutorial we built a complete operational suite that:

- **Retrieves** forecast data from MARS for multiple cycles per day
- **Processes** each forecast step through a plotting pipeline
- **Manages** dependencies so plotting waits for data retrieval
- **Deploys** tools, environments, and static data automatically via wellies

The key wellies features used were:

| Feature | Purpose |
|---------|---------|
| `wellies-quickstart` | Scaffold the project structure |
| `Config` + YAML profiles | Separate configuration from logic |
| `ToolStore` + environments | Manage software dependencies |
| `StaticDataStore` + MARS | Declare and deploy input data |
| `DeployToolsFamily` / `DeployDataFamily` | Automated initialisation tasks |

## Next steps

Here are some challenges to extend the suite further:

1. **Add a verification step** — create a new task that compares today's
   forecast plots against yesterday's and flags anomalies.
2. **Archive logs** — wrap `MainFamily` in an
   [ArchivedRepeatFamily](log_archiving.md) to manage job output files
   across repeat iterations.
3. **Add email notifications** — use the [email exit hook](exit_hook.md)
   to get notified when plotting tasks fail.
4. **Multi-host execution** — configure a second host in `host.yaml` and
   run retrievals on a data-access node while plots run on a compute node.
