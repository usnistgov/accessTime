import datetime
import importlib
import os
import platform
import shutil
import traceback
import warnings

import mcvqoe.base.version
import numpy as np


def fill_log(test_obj):
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
    tb_info = [(os.path.basename(fs.filename), fs.name if fs.name != "<module>" else None) for fs in tb]

    # add entry for calling file
    info["filename"] = tb_info[-1][0]

    # format string with '->' between files
    info["traceback"] = "->".join([f"{f}({n})" if n is not None else f for f, n in tb_info])

    # ---------------------------[Add MCV QoE version]---------------------------

    info["mcvqoe version"] = mcvqoe.base.version

    # ----------------------[Add Measurement class version]----------------------

    if test_obj.__class__.__name__ == "measure":
        # get module for test_obj
        module = test_obj.__class__.__module__
    else:
        # TESTING : print base classes
        for base in test_obj.__class__.__bases__:
            # see if we have subclassed a measure class
            if base.__name__ == "measure":
                # get module from this class
                module = base.__module__
                # we are done
                break
        else:
            # could not find module
            module = None
            warnings.warn(f"Unable to find measure class for {test_obj.__class__.__name__}", category=RuntimeWarning)

    # set default version
    info["test version"] = "Unknown"

    if module:
        # import base level module
        mod = importlib.import_module(module)
        try:
            info["test version"] = mod.version
        except AttributeError as e:
            warnings.warn(f"Unable to get version {e}", category=RuntimeWarning)
            pass
    # ------------------------------[Add OS info]------------------------------

    info["os name"] = platform.system()
    info["os release"] = platform.release()
    info["os version"] = platform.version()

    # ---------------------------[Fill Arguments list]---------------------------

    # class properties to skip in all cases
    standard_skip = ["no_log", "info", "progress_update", "rng", "user_check"]
    arg_list = []

    np.set_string_function(lambda x: f"np.ndarray(dtype={x.dtype}, shape={x.shape})")
    for k, v in vars(test_obj).items():
        if not k.startswith("_") and k not in test_obj.no_log and k not in standard_skip:
            arg_list.append(k + " = " + repr(v))
    np.set_string_function(None)

    info["Arguments"] = ",".join(arg_list)

    # -------------------------------[Return info]-------------------------------

    return info


def format_text_block(text):
    """
    format text block for log.

    This writes out a, possibly, multi line text block to the log. It is used to
    write out both pre and post test notes.

    Parameters
    ----------
    text : str
        String containing the block of text to format.
    """

    if text is None:
        return ""

    return "".join(["\t" + line + "\n" for line in text.splitlines(keepends=False)])


def pre(info={}, outdir=""):
    """
    Take in a QoE measurement class info dictionary and write pre-test to tests.log.

    ...

    Parameters
    ----------
    info : dict
        The <measurement>.info dictionary used to write to tests.log.
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

        file.write(f"\n>>{info['test']} started at {info['Tstart'].strftime('%d-%b-%Y %H:%M:%S')}\n")
        for key in info:
            if key not in skip_keys:
                file.write(f"\t{key:<{pad_len}} : {info[key]}\n")

        file.write("===Pre-Test Notes===\n")
        file.write(format_text_block(info["Pre Test Notes"]))


def post(info={}, outdir=""):
    """
    Take in a QoE measurement class info dictionary to write post-test to tests.log.

    ...

    Parameters
    ----------
    info : dict
        The <measurement>.info dictionary.
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

        # write header
        file.write(header + "\n")
        # write notes
        file.write(format_text_block(notes))
        # write end
        file.write("===End Test===\n\n")
