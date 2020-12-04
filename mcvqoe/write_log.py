import copy
import datetime
import os

def pre(info_ref={}, outdir=""):
    """
    Take in M2E class info dictionary and write pre-test to tests.log.
    
    ...
    
    Parameters
    ----------
    info_ref : dict
        The M2E.info dictionary used to write to tests.log.
    outdir : str
        The directory to write to.
    """
    
    # Create copy of dictionary(mutable) to enable deleting key/value pairs
    info = copy.deepcopy(info_ref) 
    
    # Add 'outdir' to tests.log path
    log_datadir = os.path.join(outdir, "tests.log")
    
    # Get test type header
    tst_str = ""
    if (info.get("test") == "m2e_1loc"):
        tst_str = "One Loc Test"
        del info["test"]
    elif (info.get("test") == "m2e_2loc_tx"):
        tst_str = "Tx Two Loc Test"
        del info["test"]
    elif (info.get("test") == "m2e_2loc_rx"):
        tst_str = "Rx Two Loc Test"
        del info["test"]
    else:
        tst_str = "Unknown Test"
    
    # Put datetime into proper format
    if info.get("Time") is not None:
        tnd = info.get("Time").strftime("%d-%b-%Y %H:%M:%S")
        del info["Time"]
    else:
        tnd = "{No Time Given}"
    
    # Write all necessary arguments/test params into tests.log
    with open(log_datadir, 'a') as file:
        
        file.write(f"\n>>{tst_str} started at {tnd}\n")
        file.write(f"\tTest Type  : {info.pop('Test Type', 'Not Found')}\n")
        file.write(f"\tTx Device  : {info.pop('Tx Device', 'Not Found')}\n")
        file.write(f"\tRx Device  : {info.pop('Rx Device', 'Not Found')}\n")
        file.write(f"\tSystem     : {info.pop('System', 'Not Found')}\n")
        file.write(f"\tTest Loc   : {info.pop('Test Loc', 'Not Found')}\n")
        file.write(f"\tGit Hash   : {info.pop('Git Hash', 'Not Found')}\n")
        file.write(f"\tRI Version : {info.pop('version', 'Not Found')}\n")
        file.write(f"\tRI ID      : {info.pop('id', 'Not Found')}\n")
        file.write(f"\tArguments  : ")
        for key in list(info):
            if (key != "Pre Test Notes"):
                if len(info) == 2:
                    file.write(f"{key} = '{info[key]}'")
                else:
                    file.write(f"{key} = '{info[key]}', ")
                del info[key]
        
        # Add pre and post test notes to tests.log
        if info.get("Pre Test Notes") is not None:
            # Add tabs for each newline in pretest string
            file.write("\n===Pre-Test Notes===%s" % '\t'.join(('\n'+info.get("Pre Test Notes").
                                                               lstrip()).splitlines(True)))
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
    
    with open(log_datadir, 'a') as file:
        
        if info.get("Post Test Notes") is not None:
            file.write("===Post-Test Notes===%s" % '\t'.join(('\n'+info.get("Post Test Notes").
                                                              lstrip()).splitlines(True)))
        else:
            file.write("===Post-Test Notes===\n")
            
        file.write("===End Test===\n\n")