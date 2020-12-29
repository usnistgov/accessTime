#!/usr/bin/env python

#file operations and directory listing
import os
#used for * filename expansions
import glob
#used for copy function
import shutil
#argument parsing
import argparse
#file time parsing
import datetime
#for configuration file reading
import configparser

#prefix to show that this path needs sub folders copied
recur_prefix='*'

#data directory names
data_dirs=('data','plots','proc-data','rx-data','tx-data','training',
	os.path.join('post-processed data','csv'),os.path.join('post-processed data','mat'),
	recur_prefix+os.path.join('post-processed data','wav'),
	'2loc_rx-data',recur_prefix+'2loc_tx-data')

def dir_cpy(src,dest):
	#print message
	print(f"\tChecking directory \'{src}\' for new files",flush=True)
	#set of files in source directory
	sset=set(os.listdir(src))
	#create dest if it does not exist
	os.makedirs(dest,exist_ok=True)
	#set of files in the destination directory
	dset=set(os.listdir(dest))
	#get the files that are not in dest
	cpy=sset.difference(dset)
	#find number of files to copy
	cnum=len(cpy)
	#check if we have files to copy
	if(cnum):
		print(f"\t\tFound {cnum} files to copy",flush=True)
		for count, f in enumerate(cpy, 1):
			#print status message
			if(count%100 == 0):
				print(f"\t\tCopying file {count} of {cnum}",flush=True)
			#create source and destination names
			sname=os.path.join(src,f)
			dname=os.path.join(dest,f)
			#copy file
			shutil.copyfile(sname,dname)
			#copy metadata
			shutil.copystat(sname,dname)
			
	else:
		print('\t\tUp to date',flush=True)
			
	

#function to copy unique files
def sync_files(spath,dpath,bd=True,cull=False,sunset=30,thorough=True):
	#get datetime object for current time
	current_time=datetime.datetime.now()
	#loop over files in data_dirs
	for dat in data_dirs:
		#check for directory of directory path
		if(dat.startswith(recur_prefix)):
			recur=True
			#strip recur prefix from name
			dat_d=dat[len(recur_prefix):]
		else:
			recur=False
			dat_d=dat
		#construct source name
		src=os.path.join(spath,dat_d)
		#check if source dir exists
		if(os.path.exists(src)):
			print('Checking \''+src+'\' for new files',flush=True)
			#set of files in source directory
			sset=set(os.listdir(src))
			#construct destination name
			dest=os.path.join(dpath,dat_d)			
			#check if directory name exists and source directory has files
			if(sset and not os.path.exists(dest)):
				print('Creating folder \''+dest+'\'',flush=True);
				#create folder
				os.makedirs(dest,exist_ok=True)
			if(os.path.exists(dest)):
				#set of files in the destination directory
				dset=set(os.listdir(dest))
			else:
				#empty set for dest
				dset=set()
			#check if we are decending into directories
			if(recur and thorough):
				#yes, copy everything
				#we will work out which files in subfolders to copy later
				for dir in sset:
					#create source and destination names
					sname=os.path.join(src,dir)
					dname=os.path.join(dest,dir)
                    #check if this is a directory
					if(os.path.isdir(sname)):
						#yes, copy with dir_cpy
						dir_cpy(sname,dname)
					else:
						#no, check extension
						_,ext=os.path.splitext(sname)
						#ignore case by lowering
						ext=ext.lower()
						#is this a zip file?
						if(ext == '.zip'):
							#yes, copy it
							shutil.copyfile(sname,dname)
							#and its metadata
							shutil.copystat(sname,dname)
						else:
							#no, print a message
							print(f'Skipping \'{sname}\' it is not a directory or .zip file',flush=True)
                            
			else:
				#get the files that are not in dest
				cpy=sset.difference(dset)
				#check if there are files to copy
				if cpy:
					#copy files from src to dest that are not in dest
					for f in cpy:
						#check for temp files
						if(f.endswith('TEMP.mat')):
							#print a message
							print('Skipping \''+f+'\'',flush=True)
							#skip this file
							continue
						#create source and destination names
						sname=os.path.join(src,f)
						dname=os.path.join(dest,f)
						#print message
						print('Copying \''+sname+'\' to \''+dname+'\'',flush=True)
						if recur and os.path.isdir(sname):
							#copy directory
							shutil.copytree(sname,dname)
							#TODO: copy metadata?
						else:
							#copy file
							shutil.copyfile(sname,dname)
							#copy metadata
							shutil.copystat(sname,dname)
				else:
					print('\t'+'No new files found to copy to \''+dest+'\'')
				
			#check if we need to copy in the reverse
			if(bd):
				#get the files that are not in src
				cpy=dset.difference(sset)
				#check if there are files to copy
				if cpy:
					print('\t'+'Backing files up from \''+dest+'\' to \''+src+'\'')
					#copy files from dest to src that are not in src
					for f in cpy:
						#check for temp files
						if(f.endswith('TEMP.mat')):
							#print a message
							print('Skipping \''+f+'\'',flush=True)
							#skip this file
							continue
						#create source and destination names
						sname=os.path.join(dest,f)
						dname=os.path.join(src,f)
						#check if source is a directory
						if(not recur and os.path.isdir(sname)):
							#print a message
							print('Skipping Directory \''+sname+'\'',flush=True)
							#skip this file
							continue
						#print message
						print('Copying \''+sname+'\' to \''+dname+'\'',flush=True)
						if recur:
							#copy directory
							shutil.copytree(sname,dname)
							#TODO: copy metadata?
						else:
							#copy file
							shutil.copyfile(sname,dname)
							#copy metadata
							shutil.copystat(sname,dname)
				else:
					print('\t'+'No new files found to copy to \''+src+'\'',flush=True)
			elif(cull):
				#find old files and delete them
				for f in sset:
					#strip extension off of name
					name,ext=os.path.splitext(f)
					#split name into parts
					parts=name.split('_')
					num_pts=len(parts)
					#check extension
					if(ext=='.mat'):
						if(parts[-1] in ('ERROR','TEMP')):
							date_slice=slice(num_pts-3,num_pts-1)
						elif(parts[-2]=='of'):
							date_slice=slice(num_pts-5,num_pts-3)
						else:
							date_slice=slice(num_pts-2,num_pts)
					elif(ext=='.csv'):
						date_slice=slice(num_pts-6,num_pts-4)
					else:
						date_slice=date_slice=slice(num_pts-2,num_pts)
					#grab date from filename
					dstr='_'.join(parts[date_slice])
					try:
						#parse string
						f_date=datetime.datetime.strptime(dstr,'%d-%b-%Y_%H-%M-%S')
						#calculate file age
						age=current_time-f_date
						#check if file is older than sunset days
						if(age.days>sunset):
							#create file name
							fullname=os.path.join(src,f)
							#check for directory
							if(os.path.isdir(fullname)):
								#print message
								print('Deleting old directory \''+fullname+'\'',flush=True)
								shutil.rmtree(fullname)
							else:
								#print message
								print('Deleting old file \''+fullname+'\'',flush=True)
								#delete file
								os.remove(fullname)
					except ValueError:
						print('Unable to parse date in file \''+os.path.join(src,f)+'\'',flush=True)
						
		else:
			#could not find source directory on drive, skip
			print('Source directory \''+src+'\' does not exist, skipping',flush=True)
			


#main function 
if __name__ == "__main__":
    #get path name that this file is in
    file_path=os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(description='Copy MCV data files between drive and computers')
    parser.add_argument('- i','--import', dest='imp', action='store', default=None, metavar='DIR',
                       nargs=2, help='Use to import data from a given project folder')
    parser.add_argument('--cull', dest='cull', action='store_true', default=False,
                       help='Remove old files from source directory')
    parser.add_argument('--no-cull', dest='cull', action='store_false',
                       help='Do not remove old files from source directory')
    parser.add_argument('--sunset', dest='sunset', type=int,default=30,
                       help='Delete files older than sunset days')
    parser.add_argument('--superficial', dest='thorough', action='store_false', default=False,
                       help='Don\'t decend into datadir subfolders to check if new files exist')
    parser.add_argument('--thorough', dest='thorough', action='store_true', default=False,
                       help='Decend into datadir subfolders to check if new files exist')
    parser.add_argument('-C','--config',default=os.path.join(file_path,'testCpy.cfg'),metavar='CFG',dest='config',
                        help='Path to configuration file (defaults to %(default)s)')

                       
    args = parser.parse_args()

    #check if import argument was given
    if(args.imp is None):
    
        #create a config parser
        config = configparser.ConfigParser()
        
        #load config file
        config.read(args.config)
        
        #find configuration file location, all paths are relative to this
        config_fold=os.path.dirname(os.path.abspath(args.config))
                   
        for section in config.sections():
            #print section message
            print(f'Running section {section}')
            
            #get, what should be, the relative path from config
            src_rel=config[section]['src']
            
            if(os.path.isabs(src_rel)):
                raise RuntimeError('source paths must not be absolute paths')
                
            #make path absolute
            src_dir=os.path.normpath(os.path.join(config_fold,src_rel))
            
            #print log files message
            print(f'Finding Log files in \'{src_dir}\'',flush=True);
            #list log files
            logs=glob.glob(os.path.join(src_dir,'*.log'))
            
            for l in logs:
                #get file name from path
                (h,name)=os.path.split(l)
                #generate destination filename
                dest=os.path.join(config[section]['dest'],name)
                #print message
                print('Coping \''+name+'\' into \''+dest+'\'',flush=True)
                #make sure directory exists
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                #copy log file into new directory
                shutil.copyfile(l,dest)
                #copy metadata
                shutil.copystat(l,dest)
                
            sync_files(src_dir,config[section]['dest'],thorough=args.thorough);
    else:
        #get source and destination folders from argument
        src=args.imp[0]
        dest=args.imp[1]
        #print message
        print('Copying data from \''+src+'\' to \''+dest+'\'');
        #call sync function, don't copy data in the revers direction
        sync_files(src,dest,bd=False,cull=args.cull,sunset=args.sunset);
