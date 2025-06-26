import importlib
from typing import Optional


def show_versions(as_dict: bool = False) -> Optional[dict[str, str]]:
    """
    Print the version of the wellies package.
    """
    pkgs = ["ecflow", "pyflow", "wellies", "tracksuite"]
    versions = {
        name: version
        for name, version in zip(
            pkgs, map(lambda p: importlib.import_module(p).__version__, pkgs)
        )
    }
    if as_dict:
        return versions
    else:
        print("Installed versions")
        print("------------------")
        print("\n".join([f"{k:12s}: {v:15s}" for k, v in versions.items()]))


if __name__ == "__main__":
    show_versions()
