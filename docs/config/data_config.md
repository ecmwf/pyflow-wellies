# Static data

Wellies defines static data as anything that should be made available in a common suite working environment. The data source can be local or remote. By defining different types, wellies 
will associate to the data reference a particular retrieval script. The options are:

- **link**: This only works with local data. The associated script will create a symbolic link to the source directory in the suite target directory.
- **copy**: The associated script will copy the source directory in the suite target directory. If `files` is specified, will only copy those.
- **rsync**: The associated script will rsync the source directory in the suite target directory. If `files` is specified, will only copy those. Extra options for the rsync command can be provided with `rsync_options`; the default is to use `"-avzpL"`.
- **git**: The associated script will clone a repository `branch` on the suite target directory. If `files` is specified it will clone on to a temporary directory, `git`, then rsync everything in `files`, therefore it also accepts `rsync_options`.
- **ecfs**: The associated script copies data from the `ECFS` remote archive in the suite directory. If `files` is specified it will only copy those.
- **mars**: The associated script will be a `MARS` request. All the keys should be given in the `request` option. For more details, on the MARS request option check [here](../api/data.md)
- **custom**: This is a wildcard option that natively does nothing, but the user can specify a custom script to use using options `pre_script` or `post_script`.

All scripts can be extended by using the options `pre_script` and `post_script`.

## Examples

### Link data

Configuration entry and assuming `DATA_DIR` is well a defined suite variable.

```yaml title="data.yaml"
static_data:
    large_datasets:
        type: link
        source: /path/to/dir
```

wellies data script snippet

```python exec="true" id="link_data"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.data import LinkData
ldata = LinkData("$DATA_DIR", "large_datasets", {"source": "/path/to/dir"})
script='\n'.join(ldata.script.generate_stub())
print(f"```shell\n{script}\n```" )
```

### Copy data

Configuration entry and assuming `DATA_DIR` is a well defined suite variable.

```yaml title="data.yaml"
static_data:
    copy_data:
        type: copy
        source: /path/to/dir/file.txt
        post_script: "echo 'Copy Done'"
```

wellies data script snippet

```python exec="true" id="copy_data"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.data import CopyData
ldata = CopyData("$DATA_DIR", "copy_data", {"source": "/path/to/dir/file.txt", "post_script": "echo 'Copy Done'"})
script='\n'.join(ldata.script.generate_stub())
print(f"```shell\n{script}\n```" )
```

or if using `files` option

```yaml title="data.yaml"
static_data:
    copy_data:
        type: copy
        source: /path/to/dir
        files: file.txt
        post_script: "echo 'Copy Done'"
```

The result is equivalent

```python exec="true" id="copy_files"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.data import CopyData
ldata = CopyData("$DATA_DIR", "copy_data", {"source": "/path/to/dir", "files": "file.txt", "post_script": "echo 'Copy Done'"})
script='\n'.join(ldata.script.generate_stub())
print(f"```shell\n{script}\n```" )
```

### Rsync data

Configuration entry and assuming `DATA_DIR` is a well defined suite variable. In this example, we also use `post_script` as a reference to a existing file script. If not using absolute paths, it will be relative to where the deployment has been executed.

```yaml title="data.yaml"
static_data:
    copy_data:
        type: rsync
        source: hpc-login:/path/to/dir/
        files: 
          - dis.nc
          - scov.nc
        rsync_options: "-avz"
        post_script: "install.sh"
```

wellies data script snippet

```python exec="true" id="rsync_files"
import os, sys, tempfile
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.data import RsyncData
extra_content = ["echo 'running after every other command'", "echo 'bye  bye'"]
with tempfile.TemporaryDirectory() as tmpdirname:
    with open(f"{tmpdirname}/install.sh", "w") as ftmp:
        for line in extra_content:
            ftmp.write(line + "\n")

    ldata = RsyncData(
        "$DATA_DIR", 
        "copy_data", 
        {"source": "/path/to/dir", "files": ["dis.nc", "scov.nc"], "rsync_options": "-avz", "post_script": f"{tmpdirname}/install.sh"})
    script='\n'.join(ldata.script.generate_stub())
    print(f"```shell\n{script}\n```" )
```

### Git data

Configuration entry and assuming `DATA_DIR` is a well defined suite variable.

```yaml title="data.yaml"
static_data:
  git_data:
    type: git
    source: "git.example.com/repo.git"
    branch: main
    pre_script: "git config --global user.name 'John Doe'"
```

wellies data script snippet

```python exec="true" id="git_dir"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.data import GitData
ldata = GitData("$DATA_DIR", "git_data", {"source": "git.example.com/repo.git", "branch": "main", "pre_script": "git config --global user.name 'John Doe'"})
script='\n'.join(ldata.script.generate_stub())
print(f"```shell\n{script}\n```" )
```

if `files` is specified the repository is cloned onto a temporary directory:

```yaml title="data.yaml"
static_data:
    git_data:
        type: git
        source: "git.example.com/repo.git"
        branch: main
        files:
          - static/dem.nc
          - static/metadata_template.grb
```

```python exec="true" id="git_files"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.data import GitData
ldata = GitData("$DATA_DIR", "git_data", {"source": "git.example.com/repo.git", "branch": "main", "files": ["static/dem.nc", "static/metadata_template.grb"]})
script='\n'.join(ldata.script.generate_stub())
print(f"```shell\n{script}\n```" )
```

### *ECFS* data

Configuration entry and assuming `DATA_DIR` is a well defined suite variable.

```yaml title="data.yaml"
static_data:
    ecfs_data:
        type: ecfs
        source: "ec:/path/to/data"
        post_script: "cd $DATA_DIR/ecfs_data && tar -xvf *.tar && cd -"
```

/// admonition | Note
    type: note
for remote datasets the host needs to be specified even for ECFS type.
///

wellies data script snippet

```python exec="true" id="ecfs_files"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.data import ECFSData
ldata = ECFSData("$DATA_DIR", "ecfs_data", {"source": "ec:/path/to/data", "post_script": "cd $DATA_DIR/ecfs_data && tar -xvf *.tar && cd -"})
script='\n'.join(ldata.script.generate_stub())
print(f"```shell\n{script}\n```" )
```

### *MARS* data

Configuration entry and assuming `DATA_DIR` is a well defined suite variable.

```yaml title="data.yaml"
static_data:
    mars_data:
        type: mars
        request:
          class: od
          type: an
          expver: "1"
          date: "19990215"
          time: "12"
          param: t
          levtype: "pressure level"
          levelist: [1000, 850, 700, 500]
          target: t.grb
        post_script: "pproc-interpol --grid SMUFF-OPERA-2km-proj t.grb t_2km.grb"
```

/// admonition | Note
    type: note
the *Mars* data type does not accept a `source` option.
///

wellies data script snippet

```python exec="true" id="ecfs_files"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.data import MarsData
ldata = MarsData("$DATA_DIR", "mars_data", {"request": {"class": "od", "type": "an", "expver": "1", "date": "19990215", "time": "12", "param": "t", "levtype": "pressure level", "levelist": [1000, 850, 700, 500], "target": "t.grb"}, "post_script": "pproc-interpol --grid SMUFF-OPERA-2km-proj t.grb t_2km.grb"})
script='\n'.join(ldata.script.generate_stub())
print(f"```shell\n{script}\n```" )
```

### Custom data

```yaml title="data.yaml"
static_data:
    custom_data:
        type: custom
        pre_script: "retrieve_data.sh"
        post_script: 
          - "cd $DATA_DIR/custom_data"
          - "tar -xvf *.tar"
          - "cd -"
```

wellies data script snippet

```python exec="true" id="custom_data"
import os,sys, tempfile
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.data import CustomData
extra_content = ["echo 'running data_retrieve.sh script contents'", "echo 'end of script'"]
with tempfile.TemporaryDirectory() as tmpdirname:
    with open(f"{tmpdirname}/retrieve_data.sh", "w") as ftmp:
        for line in extra_content:
            ftmp.write(line + "\n")

    ldata = CustomData(
        "$DATA_DIR",
        "custom_data",
        {"pre_script": f"{tmpdirname}/retrieve_data.sh", "post_script": ["cd $DATA_DIR/custom_data", "tar -xvf *.tar", "cd -"]}
    )
    script='\n'.join(ldata.script.generate_stub())
print(f"```shell\n{script}\n```" )
```
