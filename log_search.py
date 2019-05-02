
import os
import glob
from datetime import datetime

class log_search():
	searchPath=''
	updateMode ='Replace'
	stringSearchMode='OR'
	found=[]
	log=[]
	def __init__(self,fname,addendumName=[],LogParseAction='Warn'):
		
		if(os.path.isdir(fname)):
			#set searchpath to folder
			self.searchPath=fname;
			
			#list log files in folder
			filenames=glob.glob(os.path.join(fname,'*.log'))
			
			#create full paths
			filenames=[os.path.join(fname,n) for n in filenames];
			
			#look for adendum files
			adnames=glob.glob(os.path.join(fname,'*.ad-log'))
			
			#check if we found any files
			if(adnames):
				adnames[:]=[os.path.join(fname,n) for n in adnames]
		else:
			
			(self.searchPath,_)=os.path.split(fname)
			
			#filenames is fname
			filenames=(fname,)
			
			if(addendumName):
				adnames=(addendumName,)
			else:
				adnames=()
			
		print('Addendum Names :')
		print(adnames)
		print('Filenames :')
		print(filenames)
		
		#initialize idx
		idx=-1
		
		for fn in filenames:
			print(f'Opening file {fn}')
			with open(fn,'r') as f:
				
				#create filename without path
				(_,short_name)=os.path.split(fn)
				
				#init status
				status='searching'
				
				for lc,line in enumerate(f):
					
					print(f'Status : {status}')
					
					#strip newlines from line
					line=line.strip('\r\n')
					
					print(repr(line))
					
					if(line.startswith('>>')):
						if(status == 'searching'):
							print(f'Start of packet found at line {lc} of {short_name} while in {status} mode')
						
						#start of entry found, now we will parse the preamble
						status='preamble-st';
					
					if(status == 'searching'):
						pass
					elif(status == 'preamble-st'):
						
						#advance index
						idx+=1;
						
						#add new dictionary to list
						self.log.append({})

						#split string into date and operation
						parts=line.strip().split(' at ')

						#set date
						self.log[idx]['date']=datetime.strptime(parts[1],'%d-%b-%Y %H:%M:%S')

						#operation is the first bit
						op=parts[0]
						
						#remove >>'s from the beginning
						op=op[2:]

						#remove trailing ' started'
						if(op.endswith(' started')):
							op=op[:-len(' started')]

						#set operation
						self.log[idx]['operation']=op;

						#flag entry as incomplete
						self.log[idx]['complete']=False;

						#initialize error flag
						self.log[idx]['error']=False;

						#set source file
						self.log[idx]['logFile']=short_name;

						#dummy field for amendments
						self.log[idx]['amendedBy']='';

						#set status to preamble
						status='preamble'
					elif(status == 'preamble'):

						#check that the first character is not tab
						if(line and (not line[0]=='\t')):
							#check for three equal signs
							if(not line.startswith('===')):
								print(f'Unknown sequence found in preamble at line {lc} of file {short_name} : {line}')
								#drop back to search mode
								status='searching'
							elif(line.startswith('===End')):
								#end of entry, go into search mode
								status='searching'
								#mark entry as complete
								self.log[idx]['complete']=True;
							elif(line == '===Pre-Test Notes==='):
								status='pre-notes';
							elif(line == '===Post-Test Notes==='):
								status='post-notes';
							else:
								print(f'Unknown separator found in preamble at line {lc} of file {short_name} : {line}')
								#drop back to search mode
								status='searching'
						elif(not line):
							print('Empty line in preamble at line {lc} of file {short_name}');
						else:
							#split line on colon
							lp=line.split(':')
							#the MATLAB version uses genvarname but we just strip whitespace cause dict doesn't care
							name=lp[0].strip()
							#reconstruct the rest of line
							arg=':'.join(lp[1:])

							#check if key exists in dictionary
							if(name in self.log[idx].keys()):
								print(f'Duplicate field {name} found at line {lc} of file {short_name}')
							else:
								self.log[idx][name]=arg
								
					elif(status == 'pre-notes'):
						#check that the first character is not tab
						if(line and line[0]=='\t'):
							#check if we already have some pr_notes
							if('pre_notes' in self.log[idx]):
								#none, no separator
								sep=''
							else:
								#separate with newline
								sep='\n'
							#add in line, skip leading tab
							self.log[idx]['pre_notes']=sep+line.strip()
						else:
							#check for three equal signs
							if(not line.startswith('===')):
								print(f'Unknown sequence found at line {lc} of file {short_name} : {line}')
								#drop back to search mode
								status='searching'
							elif(line.startswith('===End')):
								#end of entry, go into search mode
								status='searching';
								#mark entry as complete
								self.log[idx]['complete']=True
							else:
								if(line == '===Post-Test Notes==='):
									status='post-notes';
									#create empty post test notes field
									self.log[idx]['post_notes']='';
								elif(line == '===Test-Error Notes==='):
									status='post-notes';
									#create empty test error notes field
									self.log[idx]['error_notes']='';
									self.log[idx]['error']=True;
								else:
									print('Unknown separator found at line {lc} of file {short_name} : {line}')
									#drop back to search mode
									status='searching';
					
					elif(status == 'post-notes'):
						#check that the first character is a tab
						if(line and line[0]=='\t'):
							field='post_notes' if(not self.log[idx]['error']) else 'error_notes'

							#set sep based on if we already have notes
							sep= '' if(field in self.log[idx]) else '\n'

							#add in line, skip leading tab
							self.log[idx][field]+=sep+line.strip()						
						else:
							#check for three equal signs
							if(not line.startswith('===')):
								print(f'Unknown sequence found at line {lc} of file {short_name} : {line}')
								#drop back to search mode
								status='searching'
							elif(line.startswith('===End')):
								#end of entry, go into search mode
								status='searching'
								#mark entry as complete
								self.log[idx]['complete']=True
							else:
								print('Unknown separator found at line {lc} of file {short_name} : {line}')
								#drop back to search mode
								status='searching'
							
							
ls=log_search('\\\\cfs2w.nist.gov\\671\\Projects\\MCV\\Access-Time\\')
#print(ls.log)

print(ls.log[-2])
