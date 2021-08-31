import datetime
import importlib
import os
import shutil
import traceback

import mcvqoe.base.version


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
    tb_info = [
        (os.path.basename(fs.filename), fs.name if fs.name != "<module>" else None) for fs in tb
    ]

    # add entry for calling file
    info["filename"] = tb_info[-1][0]

    # format string with '->' between files
    info["traceback"] = "->".join([f"{f}({n})" if n is not None else f for f, n in tb_info])

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

    # ---------------------------[Fill Arguments list]---------------------------

    # class properties to skip in all cases
    standard_skip = ["no_log", "info", "progress_update", "user_check"]
    arg_list = []

    for k, v in vars(test_obj).items():
        if not k.startswith('_') and k not in test_obj.no_log and k not in standard_skip:
            arg_list.append(k + " = " + repr(v))

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
    
    if(text is None):
        return ''
    
    return ''.join(['\t'+line+'\n' for line in text.splitlines(keepends=False)])
    
    
    
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

        file.write("===Pre-Test Notes===\n")
        file.write(format_text_block(info["Pre Test Notes"]))


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

        #write header
        file.write(header+'\n')
        # write notes
        file.write(format_text_block(notes))
        # write end
        file.write("===End Test===\n\n")
