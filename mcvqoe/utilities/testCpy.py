#!/usr/bin/env python

import os
import sys
import platform
import json
import re
import subprocess
import argparse
import pkgutil

#used for version checking
import pkg_resources
import mcvqoe


if platform.system()=='Windows':
    
    def get_drive_serial(drive):
        #run vol command, seems that you need shell=True. Perhaps vol is not a real command?
        result=subprocess.run(f'vol {drive}',shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        
        #check return code
        if(result.returncode):
            info=result.sterr.decode('UTF-8')
            
            if('the device is not ready' in info.tolower()):
                raise RuntimeError('Device is not ready')
            else:
                raise RuntimeError(f'Could not get volume info vol returnd {res.returncode}')
        
        #find drive serial number
        m=re.search('^\W*Volume Serial Number is\W*(?P<ser>(?:\w+-?)+)',result.stdout.decode('UTF-8'),re.MULTILINE)

        if(m):
            return m.group('ser')
        else:
            raise RuntimeError('Serial number not found')
        
    def list_drives():
        
        result=subprocess.run(['wmic','logicaldisk','get','name'],stdout=subprocess.PIPE)
        
        if(result.returncode):
            raise RuntimeError('Unable to list drives')
            
        drive_table=[]
            
        for line in result.stdout.decode('UTF-8').splitlines():
            #look for drive in line
            m=re.match('\A\s*(?P<drive>[A-Z]:)\s*$',line)
            #if there was a match
            if(m):
                res=subprocess.run(f'vol {m.group("drive")}',shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                
                if(res.returncode):
                    info=res.sterr.decode('UTF-8')
                    
                    if('the device is not ready' in info.tolower()):
                        #drive is not ready, skip
                        continue
                    else:
                        raise RuntimeError(f'command returnd {res.returncode} for drive \'{m.group("drive")}\'')
                
                #find drive label
                m_label=re.search(m.group('drive').rstrip(':')+'\W*(?P<sep>\w+)\W*(?P<label>.*?)\W*$',res.stdout.decode('UTF-8'),re.MULTILINE)
                
                if(m_label):
                    #dictionary with serial and label
                    info={'drive' : line.strip()}
                    #check if we got a label
                    if(m_label.groups('sep') == 'is'):
                        info['label']=m_label.groups('label')
                    else:
                        info['label']=''
                    
                    m_ser=re.search('^\W*Volume Serial Number is\W*(?P<ser>(?:\w+-?)+)',res.stdout.decode('UTF-8'),re.MULTILINE)
                    
                    if(m_ser):
                        info['serial']=m_ser.group('ser')
                    else:
                        info['serial']=''
                    
                    drive_table.append(info)
        
        return tuple(drive_table)
else:
    def list_drives():
        raise RuntimeError('Only Windows is supported at this time')
        
    def get_drive_serial(drive):
        raise RuntimeError('Only Windows is supported at this time')
    

def log_update(log_in_name,log_out_name,dryRun=False):
    with open(log_in_name,'rt') as fin:
        #will hold extra chars from input file
        #used to allow for partial line matches
        extra=''
        if(os.path.exists(log_out_name)):
            with open(log_out_name,'rt') as fout:
                for line, (lin,lout) in enumerate(zip(fin,fout),start=1):
                    #check if the last match was not a full match
                    if(extra):
                        raise RuntimeError(f'At line {line}, last line was a partial match.')
                    #check if lines are the same
                    if(lin != lout):
                        #check if lout starts with lin
                        if(lin.startswith(lout)):
                            #get the chars in lout but not lin
                            extra=lin[len(lout):]
                        else:
                            raise RuntimeError(f'Files differ at line {line}, can not copy')
                
                #get the remaining data in the file
                out_dat=fout.read()
        else:
            if(dryRun):
                #make sure that path to log file exists
                os.makedirs(os.path.dirname(log_out_name),exist_ok=True)
            #no in_dat
            in_dat=None
            
        #get remaining data in input file
        in_dat=fin.read()
        
        #strip trailing white space to prevent errors in future, add extra data 
        in_dat=extra+in_dat.rstrip()
                
        #check if we have more data from the input file 
        if(in_dat):
            
            #with open(log_out_name,'at') as fout:
            with (os.fdopen(os.dup(sys.stdout.fileno()), 'w') if dryRun else open(log_out_name,'at')) as fout:
                fout.write(in_dat)
                
            print(f'{len(in_dat.splitlines())} lines copied')
            
        else:
            if(out_dat):
                raise RuntimeError('Input file is shorter than output')
            else:
                print('Log files are identical, no lines copied')
                
    
    #print success message
    print(f'Log updated successfully to {log_out_name}\n')


#main function 
def main():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument(
                        '-d', '--dest-dir', default=None,type=str,metavar='DIR',dest='destDir',
                        help='Path to store files on removable drive')
    parser.add_argument('-o', '--outdir', default='', metavar='DIR',
                        help='Directory where test output data is stored')
    parser.add_argument("-c", "--computer-name", default=None,metavar='CNAME',dest='cname',
                        help="computer name for log file renaming")
    parser.add_argument('-s', '--sync-directory', default=None,metavar='SZ',dest='syncDir',
                        help='Directory on drive where sync script is stored')
    parser.add_argument('-D', '--dry-run', action='store_true', default=False,dest='dryRun',
                        help='Go through all the motions but, don\'t copy any files')
    parser.add_argument('-f', '--force', action='store_true', default=False,
                        help='overwrite config files with values from arguments')
    parser.add_argument('-i', '--direct', action='store_true', default=False,
                        help='Copy directly to destination, not to a HD')
                        
    #parse arguments
    args = parser.parse_args()
    
    if( args.outdir ):
        OutDir=os.getcwd()
    else:
        OutDir=args.outdir
        
    set_file=os.path.join(OutDir,'CopySettings.json')
    
    log_in_name=os.path.join(OutDir,'tests.log')
    
    if(os.path.exists(set_file)):
        
        with open(set_file,'rt') as fp_set:
            set_dict=json.load(fp_set)
        
        if('Direct' not in set_dict):
            #default direct to False
            set_dict['Direct']=False
        
        if(set_dict['Direct']):
            dest_drive_prefix=''
        else:
            drives=list_drives()
            
            drive_info=next((item for item in drives if item["serial"] == set_dict['DriveSerial']),None)
            
            if(not drive_info):
                raise RuntimeError(f'Could not find drive with serial {set_dict["DriveSerial"]}')
                
            #create drive prefix, add slash for path concatenation
            dest_drive_prefix=drive_info['drive']+os.sep
            
    else:
        if(not args.cname):
            raise RuntimeError(f'--computer-name not given and \'{set_file}\' does not exist')
        
        if(not args.destDir):
            raise RuntimeError(f'--dest-dir not given and \'{set_file}\' does not exist')
            
        #TODO : check for questionable names in path?
        
        if(args.direct):
            dest_drive_prefix=""
            rel_path=args.destDir
            drive_ser=None
        else:
            #split drive from path
            (dest_drive_prefix,rel_path)=os.path.splitdrive(args.destDir)
            
            #get serial number for drive
            drive_ser=get_drive_serial(dest_drive_prefix)
            
            #add slash for path concatenation
            dest_drive_prefix=dest_drive_prefix+os.sep
        
        #create dictionary of options, normalize paths
        set_dict={'ComputerName' : os.path.normpath(args.cname),'DriveSerial' : drive_ser,'Path' : os.path.normpath(rel_path),'Direct' : args.direct}
        
    with (os.fdopen(os.dup(sys.stdout.fileno()), 'w') if args.dryRun else open(set_file, 'w')) as sf:
        if(args.dryRun):
            print('Settings file:')
        json.dump(set_dict,sf)
    
    #file name for output log file
    log_out_name=os.path.join(dest_drive_prefix,set_dict['Path'],set_dict['ComputerName']+'-tests.log')
        
    log_update(log_in_name,log_out_name,args.dryRun)    
        
    print('Prefix : '+dest_drive_prefix)
    
    #create destination path
    destDir=os.path.join(dest_drive_prefix,set_dict['Path']);
    
    if(not set_dict['Direct']):
        
        if(args.syncDir):
            syncDir=args.syncDir
        else:
            syncDir=os.path.join(dest_drive_prefix,'sync')
            
        SyncScript=os.path.join(syncDir,'sync.py')    
        sync_ver_path=os.path.join(syncDir,'version.txt')
        
        sync_update=False
        
        if(not os.path.exists(SyncScript)):
            sync_update=True
            #print message
            print('Sync directory not found, updating');
            
        if(not sync_update):
        
            if(os.path.exists(sync_ver_path)):
                #read version from file
                with open(sync_ver_path,'r') as f:
                    sync_ver=pkg_resources.parse_version(f.read())
                
                #get version from package
                qoe_ver=pkg_resources.parse_version(mcvqoe.version)
                
                #we need to update if sync version is older than mcvqoe version
                sync_update=qoe_ver>sync_ver
                
                if(sync_update):
                    print('Sync version old, updating')
            
            else:
                sync_update=True
                print('Sync version missing, updating')
        
        if(sync_update and not args.dryRun):
            #there is no sync script
            #make sync dir
            os.makedirs(syncDir,exist_ok=True)
            #copy sync script
            with open(SyncScript,'wb') as f:
                f.write(pkgutil.get_data('mcvqoe','utilities/sync.py'))
                
            with open(sync_ver_path,'w') as f:
                f.write(mcvqoe.version)
        
        #try to get path to python
        py_path=sys.executable
        
        if(not py_path):
            #couldn't get path, try 'python' and hope for the best
            py_path='python'
        
        syncCmd=[py_path,SyncScript,'--import',OutDir,destDir,'--cull']
        
        if(args.dryRun):
            print('Calling sync command:\n\t'+' '.join(syncCmd))
        else:
            stat=subprocess.run(syncCmd)
            
            if(stat.returncode):
                raise RuntimeError(f'Failed to run sync script exit status {stat.returncode}')
    else:
        #direct sync, use library version
        from . sync import sync_files
        
        if(args.dryRun):
            print('Calling sync command:\n\t'+
                f'sync.sync_files({repr(OutDir)}, {repr(destDir)}, bd=False, cull=True, sunset=30)')
        else:
            sync_files(OutDir,destDir,bd=False,cull=True,sunset=30);
    
if __name__ == "__main__":
    main()
