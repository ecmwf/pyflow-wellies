# Suite deployment

When you create a suite using the [wellies-quickstart](quickstart_guide.md) utility, Wellies will create a *deploy.py* executable that can be used to deploy your suite. By default, the deploy script can be run as follows:

```
usage: deploy.py <CONFIG_NAME>

Generate required files for a pyflow suite project.

positional arguments:
  CONFIG_NAME           YAML configuration profile name

options:
  -h, --help            show this help message and exit
  -p CONFIG_NAME, --profiles CONFIG_NAME
                        YAML configuration profiles
  -s KEY=VALUE [KEY=VALUE ...], --set KEY=VALUE [KEY=VALUE ...]
                        Set a number of key-value pairs (do not put spaces before or after the = sign). If a value contains spaces, you should define it with double quotes: foo="this is a sentence". Note that values
                        are always treated as strings.
  -m MESSAGE, --message MESSAGE
                        Deployment git commit message
  -b BUILD_DIR, --build_dir BUILD_DIR
                        Build directory for suite deployment, by default a temporary directory is created
  -f FILES [FILES ...], --files FILES [FILES ...]
                        Specific files to deploy, by default everything is deployed
  -y                    Answers yes to all prompts
  -n, --no_deploy       Skip deployment
```

Users can then update the script to add their own deployment options and deploy the suite from [configuration files](configurations.md).

Wellies-quickstart also creates a *build.sh* shell script at the root of the project. This script allows you to load or build automatically the wellies environment that will allow you to deploy the suite. This also means the Makefile can be used to document the main deployment configurations of the suite. The script also contains a shortcut to run the tests using

```shell
./build.sh tests
```

The script can be extended to add more deployment configurations but also to create complex deployment mechanism with options depending on each other. Extra command line arguments are directly propagated to the *deploy.py* executable. For instance:

```bash
./build.sh user -m "New trigger added to the suite"
```

# Tracksuite: a suite tracking tool based on git

Wellies uses a Python library called [tracksuite](https://github.com/ecmwf/tracksuite) to handle the deployment of the suite files, *i.e.* task scripts and the definition file. Tracksuite allows to track the deployment of a suite through [Git](https://git-scm.com), allowing multiple users to collaborate on a suite and avoid conflicts between concurrent suite changes. The suite also simplifies the deployment of the suite using a different user account.

The global deployment options are specified in the suite configuration files and some command line arguments provide options related to a specific push of the suite to the deployment target.

In the *deploy.py* script, the [wellies.deploy_suite][] function takes care of interfacing with tracksuite. It is interfaced as follows in the *deploy.py* template generated by Wellies:

```python
    wl.deploy_suite(
        suite,
        user=config.user,
        name=config.name,
        hostname=config.deploy_hostname,
        deploy_dir=config.deploy_dir,
        backup_deploy=config.backup_deploy,
        build_dir=args.build_dir,
        no_prompt=args.y,
        no_deploy=args.no_deploy,
        message=args.message
    )
```

The global options come from the configuration object, which is driven by yaml configuration files (see [Deployment configuration](configurations.md)). In particular, the **backup_deploy** option allows to push the changes of the suite to a remote repository, for instance hosted on GitHub or BitBucket. This would allow users to monitor the deployment of the suite on a web interface, without having to connect directly to their deployment host.

The command line arguments provide the following dynamic options:

- **build_dir**: the build directory to store the suite files before pushing to the deployment target. This is an optional argument, if not provided the build directory will be created in the temporary space (recommended).
- **no_prompt**: when activated, this option skips all the prompt at deployment. The option is recommended if you want to deploy the suite automatically within a larger framework.
- **no_deploy**: when activated, this option writes the suite files in the build directory but does not push by default to the deployment target.
- **message**: add a comment in the Git commit. The Git commit will always contain the following message by default: `deployed by USER from HOST:BUILD_DIR`

Once the deployment options are set, users can deploy the suite through the *deploy.py* executable or through the *Makefile*.

The first time the suite is deployed, user will be prompted to create the Git repository on the deployment target:

```
Remote repository does not seem to exist. Do you want to initialise it? (N/y)
```

Once the remote repository is initialised, Tracksuite will display a summary of the changes you're about to push to the target repository. Typically:

```
Changes in staged suite:
    - Removed:
        - dummy.txt
    - Added:
        - init/deploy_data/mars_sample.ecf
        - init/deploy_data/git_sample.ecf
        - init/deploy_tools/deploy_tools.man
        - init/deploy_tools/suite_env/packages.man
        - init/deploy_tools/suite_env/earthkit.ecf
        - init/deploy_tools/suite_env/setup.ecf
        - main/dummy.ecf
        - tmp.def
For more details, compare the following folders:
/tmp/build_tmp_ce7w453u/staging
/tmp/build_tmp_ce7w453u/local
```

As displayed, users can also compare the generated files with those from the target repository using a common diff tool.

A final prompt will ask the users if they want to push the suite to the target repository:

```
------------------------------------------------------
Deploying suite to TARGET_DIR
------------------------------------------------------
You are about to push the staged suite to the target directory. Are you sure? (N/y)
```

Once deployed, users can load the suite on their ecflow server using [ecflow_client commands](https://confluence.ecmwf.int/pages/viewpage.action?pageId=52464827). Typically

```
ecflow_client --load=/TARGET_DIR/suite.def
```
