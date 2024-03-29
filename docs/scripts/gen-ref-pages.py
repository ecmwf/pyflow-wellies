"""Generate the code reference pages at build time"""

from pathlib import Path

import mkdocs_gen_files

src = Path(__file__).parent.parent.parent

for path in sorted(src.rglob("wellies/*.py")):
    module_path = path.relative_to(src).with_suffix("")
    parts = list(module_path.parts)

    doc_path = path.relative_to(src).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    if parts[-1] == "__init__":
        parts = parts[:-1]
    elif parts[-1] in ["__main__", "_version"]:
        continue

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        identifier = ".".join(parts)
        print("::: " + identifier, file=fd)

    mkdocs_gen_files.set_edit_path(full_doc_path, path)
