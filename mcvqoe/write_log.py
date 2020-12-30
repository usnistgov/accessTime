
import datetime
import os
import git
import traceback

def fill_log(test_obj):
    """
    Take in QoE measurement class and fill in standard log entries
    
    ...
    
    Parameters
    ----------
    test_obj : QoE measurement class
        Class to generate test info for
    """
    
    #initialize info
    info={}
    
    #---------------------------[RadioInterface info]---------------------------
    
    # Get ID and Version number from RadioInterface
    info['RI version']  = test_obj.ri.get_version()
    info['RI id'] = test_obj.ri.get_id()

    #------------------------------[Get Git Hash]------------------------------

    sha = ""
    try:
        repo = git.Repo(search_parent_directories=True)
        sha = repo.head.object.hexsha
    except git.exc.InvalidGitRepositoryError:
        sha = "No Git Hash Found"
    
    info["Git Hash"]=sha
    
    #---------------------[Get traceback for calling info]---------------------
    
    #get a stack trace
    tb=traceback.extract_stack()
    
    #remove the last one cause that's this function
    tb=tb[:-1]
    
    #extract important info from traceback
    tb_info=[(os.path.basename(fs.filename),fs.name if fs.name != '<module>' else None) for fs in tb]
    
    #add entry for calling file
    info['filename']=tb_info[-1][0]
    
    #format string with '->' between files
    info['traceback']='->'.join([f'{f}({n})' if n is not None else f for f,n in tb_info])
    
    #---------------------------[Fill Arguments list]---------------------------
    
    #class properties to skip in all cases
    standard_skip=['no_log','info']
    arg_list=[]
    
    for k,v in vars(test_obj).items():
        if(k not in test_obj.no_log and k not in standard_skip):
            arg_list.append(k + ' = ' + repr(v))
    
    info['Arguments']=','.join(arg_list)
    
    #-------------------------------[Return info]-------------------------------
    
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
    
    #length to pad test params to 
    pad_len=10
    
    # Add 'outdir' to tests.log path
    log_datadir = os.path.join(outdir, "tests.log")
    
    skip_keys=['test','Tstart','Pre Test Notes']
    
    # Write all necessary arguments/test params into tests.log
    with open(log_datadir, 'a') as file:
        
        file.write(f"\n>>{info['test']} started at {info['Tstart']}\n")
        for key in info:
            if (key not in skip_keys):
                file.write(f"\t{key:<{pad_len}} : {info[key]}\n")
                
        # Add pre test notes to tests.log
        if info["Pre Test Notes"] is not None:
            # Add tabs for each newline in pretest string
            file.write("\n===Pre-Test Notes===%s" % '\t'.join(('\n'+
                        info["Pre Test Notes"].lstrip()).splitlines(True))
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
    
    with open(log_datadir, 'a') as file:
        
        if info.get("Post Test Notes") is not None:
            file.write("===Post-Test Notes===%s" % '\t'.join(('\n'+info.get("Post Test Notes").
                                                              lstrip()).splitlines(True)))
        else:
            file.write("===Post-Test Notes===\n")
            
        file.write("===End Test===\n\n")