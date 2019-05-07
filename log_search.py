
import os
import glob
from datetime import datetime
import re
import subprocess
import tempfile

class log_search():
	searchPath=''
	updateMode ='Replace'
	stringSearchMode='OR'
	found=[]
	log=[]
	foundCleared=True
	fixedFields=['error','complete','operation','GitHash','logFile','amendedBy','date','Arguments','filename','InputFile','OutputFile']
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
					
					#strip newlines from line
					line=line.strip('\r\n')
					
					if(line.startswith('>>')):
						if(not status == 'searching'):
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
								print(f'Unknown sequence found in preamble at line {lc} of file {short_name} : {repr(line)}')
								#drop back to search mode
								status='searching'
							elif(line.startswith('===End')):
								#end of entry, go into search mode
								status='searching'
								#mark entry as complete
								self.log[idx]['complete']=True;
							elif(line == '===Pre-Test Notes==='):
								status='pre-notes';
								#create empty pre test notes field
								self.log[idx]['pre_notes']='';
							elif(line == '===Post-Test Notes==='):
								status='post-notes';
								#create empty post test notes field
								self.log[idx]['post_notes']='';
							else:
								print(f'Unknown separator found in preamble at line {lc} of file {short_name} : {repr(line)}')
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
							#set sep based on if we have pre_notes
							sep='\n' if(self.log[idx]['pre_notes']) else ''
								
							#add in line, skip leading tab
							self.log[idx]['pre_notes']+=sep+line.strip()
						else:
							#check for three equal signs
							if(not line.startswith('===')):
								print(f'Unknown sequence found at line {lc} of file {short_name} : {repr(line)}')
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
									print('Unknown separator found at line {lc} of file {short_name} : {repr(line)}')
									#drop back to search mode
									status='searching';
					
					elif(status == 'post-notes'):
						#check that the first character is a tab
						if(line and line[0]=='\t'):
							field='post_notes' if(not self.log[idx]['error']) else 'error_notes'

							#set sep based on if we already have notes
							sep= '' if(self.log[idx][field]) else '\n'

							#add in line, skip leading tab
							self.log[idx][field]+=sep+line.strip()						
						else:
							#check for three equal signs
							if(not line.startswith('===')):
								print(f'Unknown sequence found at line {lc} of file {short_name} : {repr(line)}')
								#drop back to search mode
								status='searching'
							elif(line.startswith('===End')):
								#end of entry, go into search mode
								status='searching'
								#mark entry as complete
								self.log[idx]['complete']=True
							else:
								print('Unknown separator found at line {lc} of file {short_name} : {repr(line)}')
								#drop back to search mode
								status='searching'
		
		for fn in adnames:
			print(f'Opening addendum file {fn}')
			with open(fn,'r') as f:
				
				#create filename without path
				(_,short_name)=os.path.split(fn)
				
				#init status
				status='searching'
				
				for lc,line in enumerate(f):
					#always check for start of entry
					if(line.startswith('>>')):
						#check if we were in search mode
						if(not status=='searching'):
							#give error when start found out of sequence
							raise ValueError(f"Start of addendum found at line {lc} of file {short_name} while in {status} mode")

						#start of entry found, now we will parse the preamble
						status='preamble-st'

					if(status == 'searching'):
						pass
					elif(status == 'preamble-st'):
					
						#split string into date and operation
						parts=line.strip().split(' at ')

						#set date
						date=datetime.strptime(parts[1],'%d-%b-%Y %H:%M:%S')

						#operation is the first bit
						op=parts[0]
						
						#remove >>'s from the beginning
						op=op[2:]

						#remove trailing ' started'
						if(op.endswith(' started')):
							op=op[:-len(' started')]

						#get index from _logMatch
						idx=self._logMatch({'date':date,'operation':op});

						if(not idx):
							raise ValueError(f"no matching entry found for '{line.strip()}' from file {short_name}")
						elif(len(idx)>1):
							raise ValueError(f"multiple matching entries found for '{line.strip()}' from file {short_name}")

						#get index from set
						idx=idx.pop()

						#check if this log entry has been amended
						if(self.log[idx]['amendedBy']):
							#indicate which file amended this entry
							self.log[idx]['amendedBy']=short_name
						else:
							ValueError(f"log entry already amended at line {lc} of '{short_name}'")

						#set status to preamble
						status='preamble';
					
					elif(status=='preamble'):

						#check that the first character is not tab
						if(line and not line[0]=='\t'):
							#check for end marker
							if(not line.startswith('<<')):
								raise ValueError(f"Unknown sequence found in entry at line {lc} of file {short_name} : {line}")
							else:
								#end of entry, go into search mode
								status='searching'
						else:
							#split line on colon
							lp=line.split(':');
							
							#the MATLAB version uses genvarname but we just strip whitespace cause dict doesn't care
							name=lp[0].strip()
							#reconstruct the rest of line
							arg=':'.join(lp[1:])
							
							#check if field is amendable
							if(name in self.fixedFields):
								raise ValueError(f"At line {lc} of file {short_name} : field '{name}' is not amendable")

							#check if field exists in structure
							if(name in self.log[idx].keys()):
								self.log[idx][name]=arg
							else:
								raise ValueError(f"Invalid field {repr(name)} at line {lc} of {short_name}")
	
	def _logMatch(self,match):
		m=set()
		for n,x in enumerate(self.log):
			eq=[False]*len(match)
			for i,k in enumerate(match.keys()):
				if(k == 'date_before'):
					eq[i]=match[k]>x['date']
				elif(k == 'date_after'):
					eq[i]=match[k]<x['date']
				else:
					try:
						val=x[k]
					except KeyError:			
						eq[i]=False
						#done here, continue
						continue
					#check for strings and handle differently
					if(isinstance(val,str)):
						if(isinstance(match[k],list)):
							str_eq=[(re.compile(s).search(val)) is not None for s in match[k]]
							if(self.stringSearchMode=='AND'):
								eq[i]=all(str_eq)
							elif(self.stringSearchMode=='OR'):
								eq[i]=any(str_eq)
							elif(self.stringSearchMode=='XOR'):
								#check if exactly one string matched
								eq[i]=(1==str_eq.count(True))
						else:
							eq[i]=re.compile(match[k]).search(val) is not None
					else:
						#fall back to equals comparison
						eq[i]=(val==match[k])
			if(all(eq)):
				m.add(n)
		return m
		
	def _foundUpdate(self,idx):
		#make idx a set
		idx=set(idx)
		if(self.foundCleared):
			self.found=idx
		else:
			if(self.updateMode=='Replace'):
				self.found=idx;
			elif(self.updateMode=='AND'):
				self.found&=idx
			elif(self.updateMode=='OR'):
				self.found|=idx
			elif(self.updateMode=='XOR'):
				self.found^=idx
			else:
				raise ValueError(f"Unknown updateMode '{self.updateMode}'")
		#clear cleared
		self.foundCleared=False
		
	def Qsearch(self,search_field,search_term):
		
		#find matching entries
		idx=self.logMatch({search_field:search_term})
		
		#update found array
		self._foundUpdate(idx)
		
		return idx
		
	def MfSearch(self,search):
		
		#search must be a dictionary
		if(not isinstance(search,dict)):
			raise ValueError("the search argument must be a dictionary")
		
		#search for matching log entries
		idx=self._logMatch(search)
		
		#update found array
		self._foundUpdate(idx)
		
		return idx
		
	def clear(self):
		#clear found
		self.found=set()
		self.foundCleared=True;
				
	def datafilenames(self):
		fn=[None]*len(self.found)
		for i,idx in enumerate(self.found):
			if(self.log[idx]['operation'] == 'Test'):
				prefix=['capture_']
				folder=['data']
			elif(self.log[idx]['operation'] == 'Training'):
				prefix=['Training_']*2
				folder=['training','data']
			elif(self.log[idx]['operation'] == 'Tx Two Loc Test'):
				prefix=['Tx_capture','capture']
				folder=['tx-data']*len(prefix)
			elif(self.log[idx]['operation'] == 'Rx Two Loc Test'):
				prefix=['Rx_capture','capture']
				folder=['rx-data']*len(prefix)
			elif(self.log[idx]['operation'].startswith('Copy')):
				fn[i]=':None'
				continue
			else:
				raise ValueError(f"Unknown operation '{self.log[idx]['operation']}'")

			if(not self.log[idx]['complete']):
				fn[i]=':Incomplete'
				continue

			if(self.log[idx]['error']):
				fn[i]=':Error'

			#get date string in file format
			date_str=self.log[idx]['date'].strftime('%d-%b-%Y_%H-%M-%S')

			for f,p in zip(folder,prefix):

				foldPath=os.path.join(self.searchPath,f)

				filenames=glob.glob(os.path.join(foldPath,p+'*'))

				match=[f for f in filenames if date_str in f ]

				if(len(match)>1):
					print(f"More than one file found matching '{date_str}' in '{f}")
					fn[i]='Multiple'
				elif(not match and fn[i] is not None):
					fn[i]=''
				elif(len(match)==1):
					fn[i]=os.path.join(foldPath,match[0])
					break
			else:
				if(fn[i] is ''):
					print(f"No matching files for '{date_str}' in '{foldPath}'")

		return fn

	def isAncestor(self,rev,repo_path,git_path=None):
		
		if(git_path is None):
			git_path='git'
			
		#generate temp dir in case we need it
		with tempfile.TemporaryDirectory() as tmpdirname:
			
			if(isGitURL(repo_path)):
				#save URL
				repo_url=repo_path
				#print message to inform the user
				print(f"Cloning : {repo_path}")
				#set repo path to temp dir
				repo_path=tmpdirname
				#clone repo
				p=subprocess.run([git_path,'clone',repo_url,repo_path],capture_output=True)
				#check return code
				if(p.returncode):
					#TODO: error
					raise RuntimeError(p.stderr)
			
			#get the full has of the commit described by rev
			p=subprocess.run([git_path,'-C',repo_path,'rev-parse','--verify',rev],capture_output=True)
			#convert to string and trim whitespace
			rev_p=p.stdout.decode("utf-8").strip()
			#check for success
			if(p.returncode):
				raise RuntimeError(f"Failed to parse rev : {rev_p}")
				
			match=[]
			
			for k,l in enumerate(self.log):
				hash=l['Git Hash'].strip()
				
				if(not hash):
					#skip this one
					continue
				
				#dump dty flag
				hash=hash.split()[0]
			
				#check that hash is valid
				p=subprocess.run([git_path,'-C',repo_path,'cat-file','-t',hash],capture_output=True)
				
				if(p.returncode):
					print(f"Could not get hash for {hash} {p.stderr.decode('utf-8').strip()}")
					#skip this one
					continue
					
				p=subprocess.run([git_path,'-C',repo_path,'show-branch','--merge-base',rev_p,hash],capture_output=True)
				#remove spaces from base
				base=p.stdout.decode("utf-8").strip()
				#check for errors
				if(p.returncode):
					print(f"Could not get the status of log entry {k} git returned : {base}")
					
				if('\n' in base and base == rev_p):
					match.append(k)
					
		self._foundUpdate(match)


	@property
	def flog(self):
		return [self.log[i] for i in self.found]
		

def isGitURL(str):
	if(str.startswith('git@')):
		return True
	elif(str.startswith('https://')):
		return True
	elif(str.startswith('http://')):
		return True
	else:
		return False
