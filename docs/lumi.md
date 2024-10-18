# Building a suite for LUMI

This tutorial will cover creating a wellies suite to run tasks on the [LUMI supercomputer](https://www.lumi-supercomputer.eu/)

## Creating the initial suite

As covered in the [quickstart tutorial](./quickstart_guide.md) we'll first create the skeleton of our project using `wellies-quickstart`. We'll create a suite called `lumiproject` in our home directory.

```console
$ wellies-quickstart -p lumiproject ~/projects/lumiproject
```

If we have a look at the folder structure created

```tree
lumiproject/
├── configs
│   ├── config.yaml
│   ├── data.yaml
│   ├── execution_contexts.yaml
│   └── tools.yaml
├── deploy.py
├── Makefile
└── suite
    └── nodes.py
```

We'll start by updating our configuration files.

### Suite setup - `config.yaml`

```yaml
# -------- Suite deployment configuration -------------------------------------
# suite
suite_name: "lumiproject"
suite_deploy_dir: "/home/username/suites/lumiproject"

# ecflow_server
ecflow_hostname: "ecflow_server.lumi.example.com
ecflow_user: "ecflow-user"
deploy_dir: "/ec/flow/directory/lumiproject"

# hpc server
hpc_hostname: "lumi-c"
hpc_user: "lumi_username"
job_out: "/scratch/project_num/lumi_username/lumiproject"
workdir: "$TMPDIR"
output_root: "/scratch/project_num/lumi_username/lumiproject"

# Github/Bitbucket remote
backup_deploy: "git@github.com:gh_username/lumiproject.git"
```

Here you can see the variables are named 


...