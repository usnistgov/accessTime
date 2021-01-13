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
def local_copy(test_names, test_type = 'access', local_path = ''):
    cfs2w = '//cfs2w.nist.gov/671/Projects/MCV'
    if(test_type == 'access'):
        parent_dir = 'Access-Time'
        pdata_dir = 'post-processed data'
        # tname = os.path.join('Access-Time','post-processed data')
    elif(test_type == 'm2e'):
        # tname = os.path.join('M2E Latency','data')
        parent_dir = 'M2E Latency'
        pdata_dir = 'data'
    elif(test_type == 'psud'):
        # tname = os.path.join('PSuD','data')
        parent_dir = 'PSuD'
        pdata_dir = 'data'
    
    
    data_path = os.path.join(cfs2w,parent_dir,pdata_dir)
    
    local_data = os.path.join(local_path,pdata_dir)
    os.makedirs(local_data,exist_ok = True)
    
    #------------------[Test CSV files]--------------------------------------------
    csv_path = os.path.join(data_path,'csv')
    csv_files = os.listdir(csv_path)
    
    for cfile in csv_files:
        cpath = os.path.join(csv_path,cfile)
        for tname in test_names:
            if(tname in cfile):
                lpath = os.path.join(local_data,'csv',cfile)
                if(not os.path.exists(lpath)):
                    print("Copying {} to {}".format(cpath,lpath))
                    shutil.copyfile(cpath, lpath)
                else:
                    print("Found locally: {}".format(lpath))
    
    #-------------------------[Cutpoint Files]----------------------------------
    for tname in test_names:
        wav_path = os.path.join(data_path,'wav',tname)
        if(not os.path.exists(wav_path)):
            warnings.warn("Test path not found in wav on network {}".format(wav_path))
        else:
            wav_files = os.listdir(wav_path)
            lppath = os.path.join(local_data,"wav",tname)
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
                    
                
        
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Copy MCV data files from cfs2w to local machine')
    parser.add_argument('-f','--test-names',
                        default = [],
                        type = str,
                        nargs = "+",
                        help = 'Tests to copy')
    
    parser.add_argument('-t','--test-type',
                        default = 'access',
                        type = str,
                        help = 'Type of test to copy from (m2e,access,psud)')
    parser.add_argument('-l','--local-path',
                        default = '',
                        type = str,
                        help = "Local path to copy to")
    
    args = parser.parse_args()
    
    um = local_copy(args.test_names,
                    test_type = args.test_type,
                    local_path = args.local_path)
