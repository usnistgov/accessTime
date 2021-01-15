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

appname = 'mcvqoe'
appauthor = 'MCV'


def local_copy(test_names, test_type, local_path = None,network_path = None):
    
    #---------------[Load Config File]----------------------------------------
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
    
    # Make local path if it doesn't exist
    os.makedirs(local_path,exist_ok = True)
    
    #------------------[Test CSV files]--------------------------------------------
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
    
    #-------------------------[Cutpoint Files]----------------------------------
    for tname in test_names:
        wav_path = os.path.join(network_path,'wav',tname)
        if(not os.path.exists(wav_path)):
            warnings.warn("Test path not found in wav on network {}".format(wav_path))
        else:
            wav_files = os.listdir(wav_path)
            lppath = os.path.join(local_path,"wav",tname)
            os.makedirs(lppath,exist_ok=True)
            for wfile in wav_files:
                if(".csv" in wfile):    
                    wpath = os.path.join(wav_path,wfile)
                    lpath = os.path.join(lppath,wfile)
                    if(not os.path.exists(lpath)):
                        print("Copying {} to {}".format(wpath,lpath))
                        shutil.copyfile(wpath, lpath)
                    else:
                        print("Found locally: {}".format(lpath))

def update_config(test_type, local_path, network_path):
    # Make application directories if they do not exist
    os.makedirs(appdirs.user_data_dir(appname,appauthor),exist_ok=True)
    
    #create a config parser
    config = configparser.ConfigParser()
    
    #load config file
    config_path = os.path.join(appdirs.user_data_dir(appname,appauthor),"config.ini")
    config.read(config_path)
    
    
    config[test_type] = {'network_path': network_path,
                         'local_path': local_path}

    with open(config_path,'w') as configfile:
        config.write(configfile)

def main():
    parser = argparse.ArgumentParser(description='Copy MCV data files from cfs2w to local machine')
    parser.add_argument('-f','--test-names',
                        default = [],
                        type = str,
                        nargs = "+",
                        help = 'Tests to copy')
    
    parser.add_argument('-t','--test-type',
                        default = None,
                        type = str,
                        help = 'Type of test to copy from (m2e,access,psud)')
    parser.add_argument('-l','--local-path',
                        default = None,
                        type = None,
                        help = "Local path to copy to")
    
    parser.add_argument('-n','--network-path',
                        default = None,
                        type = str,
                        help = "Network path to copy from")
    
    
    args = parser.parse_args()
    
    if(args.test_type is None):
        raise ValueError('test_type is required')
    
    um = local_copy(args.test_names,
                    test_type = args.test_type,
                    local_path = args.local_path,
                    network_path = args.network_path)
if __name__ == "__main__":
    main()

