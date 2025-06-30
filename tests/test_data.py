# flake8: noqa
import os
from textwrap import dedent

import wellies.data as wl


def test_rsync_data_default():
    data_dir = os.path.join("path", "to", "data")
    name = "rsync_data"
    options = {
        "pre_script": "echo before rsync default",
        "type": "rsync",
        "source": os.path.join("dir", "to", "sync"),
        "post_script": "echo after rsync default",
    }

    data = wl.RsyncData(data_dir, name, options)

    ref_script = dedent(
        f"""\
        # Pre-script
        {options["pre_script"]}

        # Main script for retrieving data
        mkdir -p {data_dir}

        dest_dir={data_dir}/{name}
        rsync -avzpL {options["source"]}  $dest_dir/
        cd $dest_dir

        # Post-script
        {options["post_script"]}
    """
    )

    print("------------------")
    print("output:")
    print("------------------")
    print(data.script.value)
    print("------------------")
    print("ref:")
    print("------------------")
    print(ref_script)
    assert data.script.value == ref_script


def test_rsync_data():
    data_dir = os.path.join("path", "to", "data")
    name = "rsync_data"
    options = {
        "type": "rsync",
        "source": os.path.join("dir", "to", "sync"),
        "rsync_options": "-avz",
        "post_script": "echo after rsync",
    }

    data = wl.RsyncData(data_dir, name, options)

    ref_script = dedent(
        f"""\
        # Main script for retrieving data
        mkdir -p {data_dir}

        dest_dir={data_dir}/{name}
        rsync -avz {options["source"]}  $dest_dir/
        cd $dest_dir

        # Post-script
        {options["post_script"]}
    """
    )

    print("------------------")
    print("output:")
    print("------------------")
    print(data.script.value)
    print("------------------")
    print("ref:")
    print("------------------")
    print(ref_script)
    assert data.script.value == ref_script


def test_copy():
    data_dir = os.path.join("path", "to", "data")
    name = "rsync_data"
    options = {
        "type": "rsync",
        "source": os.path.join("file", "to", "copy.txt"),
        "post_script": "echo after copy",
    }

    data = wl.CopyData(data_dir, name, options)

    ref_script = dedent(
        f"""\
        # Main script for retrieving data
        mkdir -p {data_dir}

        dest_dir={data_dir}/{name}
        rm -rf $dest_dir
        mkdir -p $dest_dir
        scp {options["source"]}  $dest_dir/
        cd $dest_dir

        # Post-script
        {options["post_script"]}
    """
    )
    print("------------------")
    print("output:")
    print("------------------")
    print(data.script.value)
    print("------------------")
    print("ref:")
    print("------------------")
    print(ref_script)
    assert data.script.value == ref_script


def test_git_data():
    data_dir = os.path.join("path", "to", "data")
    name = "git_data"
    options = {
        "type": "git",
        "source": "git.example.com/repo.git",
        "branch": "main",
        "post_script": "echo after git",
    }

    data = wl.GitData(data_dir, name, options)

    ref_script = dedent(
        f"""\
        # Main script for retrieving data
        mkdir -p {data_dir}

        dest_dir={data_dir}/{name}
        rm -rf $dest_dir
        giturl={options["source"]}
        gitbranch={options["branch"]}
        git clone $giturl --branch $gitbranch --single-branch --depth 1 $dest_dir
        cd $dest_dir

        # Post-script
        {options["post_script"]}
    """
    )

    print("------------------")
    print("output:")
    print("------------------")
    print(data.script.value)
    print("------------------")
    print("ref:")
    print("------------------")
    print(ref_script)
    assert data.script.value == ref_script


def test_git_data_custom_build_dir():
    data_dir = os.path.join("path", "to", "data")
    build_dir = "/tmp/build"
    name = "git_data"
    options = {
        "type": "git",
        "source": "git.example.com/repo.git",
        "branch": "main",
        "build_dir": build_dir,
        "post_script": "echo after git",
    }

    data = wl.GitData(data_dir, name, options)

    ref_script = dedent(
        f"""\
        # Main script for retrieving data
        mkdir -p {data_dir}

        dest_dir={build_dir}/{name}
        rm -rf $dest_dir
        giturl={options["source"]}
        gitbranch={options["branch"]}
        git clone $giturl --branch $gitbranch --single-branch --depth 1 $dest_dir
        cd $dest_dir

        # Post-script
        {options["post_script"]}
    """
    )

    print("------------------")
    print("output:")
    print("------------------")
    print(data.script.value)
    print("------------------")
    print("ref:")
    print("------------------")
    print(ref_script)
    assert data.script.value == ref_script


def test_git_data_files():
    data_dir = os.path.join("path", "to", "data")
    name = "git_data"
    options = {
        "type": "git",
        "source": "git.example.com/repo.git",
        "branch": "main",
        "files": ["environment.yml", "requirements.txt", "static/logo.png"],
    }

    data = wl.GitData(data_dir, name, options)
    build_dir = os.path.join(data_dir, "git", name)
    file_paths = [os.path.join(build_dir, f) for f in options["files"]]

    ref_script = dedent(
        f"""\
        # Main script for retrieving data
        mkdir -p {data_dir}

        dest_dir={build_dir}
        rm -rf $dest_dir
        giturl={options["source"]}
        gitbranch={options["branch"]}
        git clone $giturl --branch $gitbranch --single-branch --depth 1 $dest_dir
        cd $dest_dir


        dest_dir={data_dir}/{name}
        rsync -avzpL {" ".join(file_paths)}  $dest_dir/
        cd $dest_dir

        echo 'cleaning build directory'
        rm -rf {build_dir}"""
    )

    print("------------------")
    print("output:")
    print("------------------")
    print(data.script.value)
    print("------------------")
    print("ref:")
    print("------------------")
    print(ref_script)
    assert data.script.value == ref_script


def test_git_data_post_script(tmp_path):
    data_dir = os.path.join("path", "to", "data")
    name = "git_data"

    extra_script = f"{tmp_path.as_posix()}/dummy.sh"
    extra_content = [
        "echo 'running after every other command'",
        "echo 'bye  bye'",
    ]
    with open(extra_script, "w") as ftmp:
        for line in extra_content:
            ftmp.write(line + "\n")
    options = {
        "type": "git",
        "source": "git.example.com/repo.git",
        "branch": "main",
        "post_script": f"{extra_script}",
    }

    data = wl.GitData(data_dir, name, options)

    extra_lines = "\n".join(extra_content)
    ref_script = dedent(
        f"""\
        # Main script for retrieving data
        mkdir -p {data_dir}

        dest_dir={data_dir}/{name}
        rm -rf $dest_dir
        giturl={options["source"]}
        gitbranch={options["branch"]}
        git clone $giturl --branch $gitbranch --single-branch --depth 1 $dest_dir
        cd $dest_dir

        # Post-script
    """
    )
    ref_script += extra_lines + "\n\n"

    print("------------------")
    print("output:")
    print("------------------")
    print(data.script.value)
    print("------------------")
    print("ref:")
    print("------------------")
    print(ref_script)
    assert data.script.value == ref_script


def test_ecfs_data():
    data_dir = os.path.join("path", "to", "data")
    name = "ecfs_data"
    options = {
        "type": "ecfs",
        "source": "ec:/path/to/data",
        "post_script": "echo after ecfs",
    }

    data = wl.ECFSData(data_dir, name, options)

    ref_script = dedent(
        f"""\
        # Main script for retrieving data
        mkdir -p {data_dir}

        dest_dir={data_dir}/{name}
        rm -rf $dest_dir
        mkdir -p $dest_dir
        ecp {options["source"]}  $dest_dir/
        cd $dest_dir

        # Post-script
        {options["post_script"]}
    """
    )
    print("------------------")
    print("output:")
    print("------------------")
    print(data.script.value)
    print("------------------")
    print("ref:")
    print("------------------")
    print(ref_script)
    assert data.script.value == ref_script


def test_ecfs_data_multiple_files():
    data_dir = os.path.join("path", "to", "data")
    name = "ecfs_data"
    options = {
        "type": "ecfs",
        "source": "ec:/path/to/data",
        "files": ["file1", "file2"],
    }

    data = wl.ECFSData(data_dir, name, options)

    ref_script = dedent(
        f"""\
        # Main script for retrieving data
        mkdir -p {data_dir}

        dest_dir={data_dir}/{name}
        rm -rf $dest_dir
        mkdir -p $dest_dir
        ecp {options["source"]}/{options['files'][0]} {options["source"]}/{options['files'][1]}  $dest_dir/
        cd $dest_dir
    """
    )
    print("------------------")
    print("output:")
    print("------------------")
    print(data.script.value)
    print("------------------")
    print("ref:")
    print("------------------")
    print(ref_script)
    assert data.script.value == ref_script


def test_ecfs_data_single_file():
    data_dir = os.path.join("path", "to", "data")
    name = "ecfs_data"
    options = {"type": "ecfs", "source": "ec:/path/to/data", "files": "file1"}

    data = wl.ECFSData(data_dir, name, options)

    ref_script = dedent(
        f"""\
        # Main script for retrieving data
        mkdir -p {data_dir}

        dest_dir={data_dir}/{name}
        rm -rf $dest_dir
        mkdir -p $dest_dir
        ecp {options["source"]}/{options['files']}  $dest_dir/
        cd $dest_dir
    """
    )
    print("------------------")
    print("output:")
    print("------------------")
    print(data.script.value)
    print("------------------")
    print("ref:")
    print("------------------")
    print(ref_script)
    assert data.script.value == ref_script


def test_link_data():
    data_dir = os.path.join("path", "to", "data")
    name = "link_data"
    options = {
        "type": "link",
        "source": "/path/to/link",
        "post_script": "echo hello",
    }

    data = wl.LinkData(data_dir, name, options)

    ref_script = dedent(
        f"""\
        # Main script for retrieving data
        mkdir -p {data_dir}

        dest_dir={data_dir}/{name}
        rm -rf $dest_dir
        ln -sfn {options["source"]} $dest_dir
        if [[ -L $dest_dir && -d $(readlink $dest_dir) ]]; then
            echo Link and directory exist
        else
            echo Link or directory does not exist
            exit 1
        fi
        cd $dest_dir

        # Post-script
        {options["post_script"]}
    """
    )

    print("------------------")
    print("output:")
    print("------------------")
    print(data.script.value)
    print("------------------")
    print("ref:")
    print("------------------")
    print(ref_script)
    assert data.script.value == ref_script


def test_mars_data():
    data_dir = os.path.join("path", "to", "data")
    name = "mars_data"
    options = {
        "type": "mars",
        "request": {
            "class": "od",
            "type": "an",
            "expver": "1",
            "date": "19990215",
            "time": "12",
            "param": "t",
            "levtype": "pressure level",
            "levelist": [1000, 850, 700, 500],
            "target": "t.grb",
        },
        "post_script": "echo hello",
    }

    data = wl.MarsData(data_dir, name, options)

    ref_script = dedent(
        f"""\
        # Main script for retrieving data
        mkdir -p {data_dir}
        dest_dir={data_dir}/{name}
        mkdir -p $dest_dir
        cd $dest_dir

        mars << EOF
        retrieve,
          class=od,
          type=an,
          expver=1,
          date=19990215,
          time=12,
          param=t,
          levtype=pressure level,
          levelist=1000/850/700/500,
          target="t.grb"
        EOF

        # Post-script
        {options["post_script"]}
    """
    )

    print("------------------")
    print("output:")
    print("------------------")
    print(data.script.value)
    print("------------------")
    print("ref:")
    print("------------------")
    print(ref_script)
    assert data.script.value == ref_script


def test_static_data_store():
    data_dir = os.path.join("path", "to", "data")
    static_data_dict = {
        "rsync_data": {
            "type": "rsync",
            "source": os.path.join("dir", "to", "sync"),
            "post_script": "echo hello",
        },
        "git_data": {
            "type": "git",
            "source": "git.example.com/repo.git",
            "branch": "main",
        },
        "ecfs_data": {"type": "ecfs", "source": "ec:/path/to/data"},
        "link_data": {"type": "link", "source": "/path/to/link"},
        "custom_data": {"type": "custom", "post_script": "echo hello"},
    }

    data_store = wl.StaticDataStore(data_dir, static_data_dict)

    ref_class = {
        "rsync_data": wl.RsyncData,
        "git_data": wl.GitData,
        "ecfs_data": wl.ECFSData,
        "link_data": wl.LinkData,
        "custom_data": wl.CustomData,
    }

    for name, data in data_store.items():
        assert isinstance(data, ref_class[name])
