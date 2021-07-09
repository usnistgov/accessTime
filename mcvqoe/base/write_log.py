import datetime
import importlib
import os
import shutil
import subprocess
import traceback

import mcvqoe.base.version


def fill_log(test_obj, git_path=None):
    """
    Take in QoE measurement class and fill in standard log entries

    ...

    Parameters
    ----------
    test_obj : QoE measurement class
        Class to generate test info for
    git_path : string, default=None
        path to git executable. Will look in the path if None
    """

    # initialize info
    info = {}

    # ---------------------------[RadioInterface info]---------------------------

    try:
        # Get ID and Version number from RadioInterface
        info["RI version"] = test_obj.ri.get_version()
        info["RI id"] = test_obj.ri.get_id()
    except AttributeError:
        # no RI for this object
        pass

    # ---------------------[Get traceback for calling info]---------------------

    # get a stack trace
    tb = traceback.extract_stack()

    # remove the last one cause that's this function
    tb = tb[:-1]

    # extract important info from traceback
    tb_info = [
        (os.path.basename(fs.filename), fs.name if fs.name != "<module>" else None) for fs in tb
    ]

    # add entry for calling file
    info["filename"] = tb_info[-1][0]

    # format string with '->' between files
    info["traceback"] = "->".join([f"{f}({n})" if n is not None else f for f, n in tb_info])

    # ------------------------------[Get Git Hash]------------------------------

    if git_path is None:
        # try to find git
        git_path = shutil.which("git")

    if git_path:
        repo_path = os.path.dirname(tb[-1].filename)

        # get the full has of the commit described by rev
        p = subprocess.run(
            [git_path, "-C", repo_path, "rev-parse", "--verify", "HEAD"],
            capture_output=True,
        )

        # convert to string and trim whitespace
        rev = p.stdout.decode("utf-8").strip()

        # check for error
        if (p.returncode) == 0:

            # check if there are local mods
            mods_p = subprocess.run(
                [git_path, "-C", repo_path, "diff-index", "--quiet", "HEAD", "--"],
                capture_output=True,
            )

            if mods_p.returncode:
                dirty = " dty"
            else:
                dirty = ""

            # set info
            info["Git Hash"] = rev + dirty

    # ---------------------------[Add MCV QoE version]---------------------------

    info["mcvqoe version"] = mcvqoe.base.version

    # ----------------------[Add Measurement class version]----------------------

    # get module for test_obj
    module = test_obj.__class__.__module__

    # set default version
    info["version"] = "Unknown"

    if module:
        # import base level module
        mod = importlib.import_module(module)
        try:
            info["version"] = mod.version
        except AttributeError as e:
            pass

    # check if version was found
    if info["version"] == "Unknown":
        # no module was found, let's try git
        # see if we found git before
        if git_path:
            # we did, use repo_path from before

            # get version from git describe
            p = subprocess.run(
                [
                    git_path,
                    "-C",
                    repo_path,
                    "describe",
                    "--match=v*.*",
                    "--always",
                    "--dirty=-dty",
                ],
                capture_output=True,
            )

            if p.returncode == 0:
                # get version from output
                info["version"] = p.stdout.decode("utf-8").strip()

    # ---------------------------[Fill Arguments list]---------------------------

    # class properties to skip in all cases
    standard_skip = ["no_log", "info"]
    arg_list = []

    for k, v in vars(test_obj).items():
        if k not in test_obj.no_log and k not in standard_skip:
            arg_list.append(k + " = " + repr(v))

    info["Arguments"] = ",".join(arg_list)

    # -------------------------------[Return info]-------------------------------

    return info


def pre(info={}, outdir=""):
    """
    Take in M2E class info dictionary and write pre-test to tests.log.

    ...

    Parameters
    ----------
    info : dict
        The M2E.info dictionary used to write to tests.log.
    outdir : str
        The directory to write to.
    """

    # length to pad test params to
    pad_len = 10

    # Add 'outdir' to tests.log path
    log_datadir = os.path.join(outdir, "tests.log")

    skip_keys = ["test", "Tstart", "Pre Test Notes"]

    # Write all necessary arguments/test params into tests.log
    with open(log_datadir, "a") as file:

        file.write(
            f"\n>>{info['test']} started at {info['Tstart'].strftime('%d-%b-%Y %H:%M:%S')}\n"
        )
        for key in info:
            if key not in skip_keys:
                file.write(f"\t{key:<{pad_len}} : {info[key]}\n")

        # Add pre test notes to tests.log
        if info["Pre Test Notes"] is not None:
            # Add tabs for each newline in pretest string
            file.write(
                "===Pre-Test Notes===%s"
                % "\t".join(("\n" + info["Pre Test Notes"].lstrip()).splitlines(True))
            )
        else:
            file.write("\n===Pre-Test Notes===\n")


def post(info={}, outdir=""):
    """
    Take in M2E class info dictionary to write post-test to tests.log.

    ...

    Parameters
    ----------
    info : dict
        The M2E.info dictionary.
    outdir : str
        The directory to write to.

    """

    # Add 'outdir' to tests.log path
    log_datadir = os.path.join(outdir, "tests.log")

    with open(log_datadir, "a") as file:
        if "Error Notes" in info:
            notes = info["Error Notes"]
            header = "===Test-Error Notes==="
        else:
            header = "===Post-Test Notes==="
            notes = info.get("Post Test Notes", "")

        # indent notes
        notes = "\t".join(("\n" + notes.strip()).splitlines(True))
        # write notes
        file.write(header + notes + "\n")
        # write end
        file.write("===End Test===\n\n")
