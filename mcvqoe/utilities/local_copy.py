# -*- coding: utf-8 -*-
"""
Created on Wed Jan 13 14:07:46 2021

@author: jkp4
"""
import os
import argparse
import pdb
import shutil
import warnings
import appdirs
import configparser
import re 

appname = 'mcvqoe'
appauthor = 'MCV'


def local_copy(test_names, test_type, local_path = None,network_path = None, tx_wav = False):
    """
    Function to copy MCV QoE Measurement Data.
    
    Stores local_path and network_path for each test_type in a config file so 
    they only need to be set once.
    
    Parameters
    ----------
    test_names : list
        Basenames of  tests.
    test_type : str
        Type of test (e.g. access, m2e, psud).
    local_path : str, optional
        Path where local data should be copied to. If None is passed, 
        local_path is found from a config file. It must have been initialized 
        for the given test type previously.
    network_path : str, optional
        Path where network data is copied from. If None is passed, 
        network_path is found from a config file. It must have been initialzed
        for the given test type previously.
    tx_wav : bool
        Indicate whether or not to copy transmit audio wav file associated 
        with cutpoints.

    Returns
    -------
    None.

    """
    #---------------------[Load Config File]----------------------------------
    # Make application directories if they do not exist
    os.makedirs(appdirs.user_data_dir(appname,appauthor),exist_ok=True)
    
    #create a config parser
    config = configparser.ConfigParser()
    
    #load config file
    config_path = os.path.join(appdirs.user_data_dir(appname,appauthor),"config.ini")
    config.read(config_path)
    

    if(network_path is None):
        # No network path passed, pull from config file if we can
        if(config.has_option(test_type,'network_path')):
            network_path = config[test_type]['network_path']
        else:
            raise ValueError('No network path passed and has not been configured')
    else:
        # If new network path passed update config file
        if(config.has_section(test_type)):    
            config[test_type]['network_path'] = network_path
        else:
            config[test_type] = {"network_path": network_path}
    
    if(local_path is None):
        # No local path passed, pull from config file if we can
        if(config.has_option(test_type,'local_path')):
            local_path = config[test_type]['local_path']
        else:
            raise ValueError('No local path passed and has not been configured')
    else:
        # If new local path passed update config file
        if(config.has_section(test_type)):
            config[test_type]['local_path'] = local_path
        else:
            # Don't think we can hit this because network path goes first...
            config[test_type] = {"local_path": local_path}
    #---------------------[Write config file]---------------------------------
    with open(config_path,'w') as configfile:
        config.write(configfile)
        
    # Make local path if it doesn't exist
    os.makedirs(local_path,exist_ok = True)
    
    #--------------------[Test CSV files]--------------------------------------------
    csv_path = os.path.join(network_path,'csv')
    csv_files = os.listdir(csv_path)
    
    for cfile in csv_files:
        cpath = os.path.join(csv_path,cfile)
        for tname in test_names:
            if(tname in cfile):
                lpath = os.path.join(local_path,'csv',cfile)
                if(not os.path.exists(lpath)):
                    print("Copying {} to {}".format(cpath,lpath))
                    shutil.copyfile(cpath, lpath)
                else:
                    print("Found locally: {}".format(lpath))
    
    #--------------------[Cutpoint Files]----------------------------------
    for tname in test_names:
        #Remmove R if reprocessed data
        tname = tname.replace('Rcapture','capture')
        # Path to wav folder
        wav_path = os.path.join(network_path,'wav',tname)
        if(not os.path.exists(wav_path)):
            warnings.warn("Test path not found in wav on network {}".format(wav_path))
        else:
            # Get all files in wav_path
            wav_files = os.listdir(wav_path)
            
            # Define local path to store wav files, make it if need be
            lppath = os.path.join(local_path,"wav",tname)
            os.makedirs(lppath,exist_ok=True)
            for wfile in wav_files:
                #TODO: Add ability to copy tx_wav
                if(".csv" in wfile):
                    # Copy cut point file
                    wpath = os.path.join(wav_path,wfile)
                    lpath = os.path.join(lppath,wfile)
                    if(not os.path.exists(lpath)):
                        print("Copying {} to {}".format(wpath,lpath))
                        shutil.copyfile(wpath, lpath)
                    else:
                        print("Found locally: {}".format(lpath))
                    #------------[Transmit Audio]-----------------------------
                    # Copy Tx wav file if option set
                    if(tx_wav):
                        wfile_no_ext,_ = os.path.splitext(wfile)
                        # Remove R is reprocessed data
                        tx_wav_wfile = wfile_no_ext + ".wav"
                        
                        # Copy from path
                        tx_wpath = os.path.join(wav_path,tx_wav_wfile)
                        # Copy to path
                        tx_lpath = os.path.join(lppath,tx_wav_wfile)
                        # Check if file already exists
                        if(not os.path.exists(tx_lpath)):
                            print("Copying {} to {}".format(tx_wpath,tx_lpath))
                            shutil.copyfile(tx_wpath,tx_lpath)
                        else:
                            print("Found locally: {}".format(tx_lpath))
                        


def print_config(test_type=None):
    """
    Print the test_types and paths stored by local_copy.

    Parameters
    ----------
    test_type : str, optional
        If given, prints paths only for that test_type. The default is None.

    Returns
    -------
    None.

    """
    #---------------------[Load Config File]----------------------------------
    # Make application directories if they do not exist
    os.makedirs(appdirs.user_data_dir(appname,appauthor),exist_ok=True)
    
    #create a config parser
    config = configparser.ConfigParser()
    
    #load config file
    config_path = os.path.join(appdirs.user_data_dir(appname,appauthor),"config.ini")
    config.read(config_path)
    
    ttype_str = '----{}----'
    path_str = '{}: {}'
    if(test_type is not None):
        print(ttype_str.format(test_type))
        for kv in config[test_type].keys():
            print(path_str.format(kv,config[test_type][kv]))
    else:
        for tt in config.keys():
            print(ttype_str.format(tt))
            for kv in config[tt].keys():
                print(path_str.format(kv,config[tt][kv]))
def convert_log_search_names(fnames):
    """
    Convert output from mcvqoe.utilities.log_search datafilenames() to what local-copy expects

    Parameters
    ----------
    fnames : TYPE
        DESCRIPTION.

    Returns
    -------
    lc_names : TYPE
        DESCRIPTION.

    """
    if(type(fnames) is str):
        fnames = [fnames]
    lc_names = []
    for fn in fnames:
        _,short_name = os.path.split(fn)
        #TODO: Make this work with an optional non-capturing group for audio file...
        # thought that '(capture_.+)(?:_\w{2}_b\d{1,2}_w\d{1}_\w+)?(?:.csv)' should work but it doesn't
        # re_search = '(capture_.+)(?:_\w{2}_b\d{1,2}_w\d{1}_\w+)(?:.csv)'
        re_search = '(R?capture_.+\d{2}-\d{2}-\d{2}).*.csv'
        # Extract part of the name that local-copy expects
        rs = re.search(re_search,short_name)
        if(rs):
            f_id = rs.groups()
            lc_names.append(f_id[0])
            
    return lc_names
def main():
    parser = argparse.ArgumentParser(description='Copy data files from network drive to local machine')
    parser.add_argument('-f','--test-names',
                        default = [],
                        type = str,
                        nargs = "+",
                        help = 'Tests to copy')
    
    parser.add_argument('-t','--test-type',
                        default = None,
                        type = str,
                        help = 'Type of test to copy from')
    parser.add_argument('-l','--local-path',
                        default = None,
                        type = None,
                        help = "Local path to copy to. If not passed read from last path used for this test-type.")
    
    parser.add_argument('-n','--network-path',
                        default = None,
                        type = str,
                        help = "Network path to copy from. If not passed read from last path used for this test-type.")
    parser.add_argument('-p','--print-config',
                       default = False,
                       action='store_true',
                       help = "Print current config file settings") 
    
    parser.add_argument('-w','--tx-wav',
                        default = False,
                        action = 'store_true',
                        help = 'Copy transmit audio wav file with cutpoints')
    
    args = parser.parse_args()
    
    if(args.print_config):
        print_config(test_type=args.test_type)
    if(args.test_names != []):
        
        if(args.test_type is None and not args.print_config):
            raise ValueError('test_type is required')
        
        local_copy(args.test_names,
                        test_type = args.test_type,
                        local_path = args.local_path,
                        network_path = args.network_path,
                        tx_wav = args.tx_wav)
if __name__ == "__main__":
    main()

