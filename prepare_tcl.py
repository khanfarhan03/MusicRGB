"""Make the base Python Tcl/Tk scripts available beside this project."""
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import zipfile


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".tcl-runtime"


def _copy_library(base, names, archive_pattern, archive_prefix, target_name):
    target = RUNTIME / target_name
    for name in names:
        source = base / "tcl" / name
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
            return target
    archives = sorted((base / "tcl").glob(archive_pattern))
    if archives:
        prefix = archive_prefix + "/"
        with zipfile.ZipFile(archives[-1]) as archive:
            for item in archive.infolist():
                if item.filename.startswith(prefix) and not item.is_dir():
                    relative = PurePosixPath(item.filename[len(prefix):])
                    destination = target.joinpath(*relative.parts)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(archive.read(item))
            if (target / "init.tcl").is_file():
                return target
    raise FileNotFoundError(f"Could not find Tcl/Tk scripts under {base / 'tcl'}")


def configure_tcl():
    base = Path(sys.base_prefix)
    tcl = _copy_library(base, ("tcl9.0", "tcl8.6"), "libtcl*.zip",
                        "tcl_library", "tcl_library")
    tk = _copy_library(base, ("tk9.0", "tk8.6"), "libtk*.zip",
                       "tk_library", "tk_library")
    return {"TCL_LIBRARY": str(tcl), "TK_LIBRARY": str(tk)}


if __name__ == "__main__":
    environment = configure_tcl()
    print(environment["TCL_LIBRARY"])
    print(environment["TK_LIBRARY"])
