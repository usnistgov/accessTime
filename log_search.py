
import os
import glob
from datetime import datetime
import re
import subprocess
import tempfile
import shutil
import stat
import warnings

class log_search():
	searchPath=''
	updateMode ='Replace'
	stringSearchMode='OR'
	found=[]
	log=[]
	foundCleared=True
	fixedFields=['error','complete','operation','GitHash','logFile','amendedBy','date','Arguments','filename','InputFile','OutputFile']
	def __init__(self,fname,addendumName=[],LogParseAction='Warn'):
		
		if(LogParseAction=='Warn'):
			msgFcn= lambda m: warnings.warn(RuntimeWarning(m),stacklevel=3)
		elif(LogParseAction=='Error'):
			def errMsg(e):
				raise RuntimeError(e)
			msgFcn=errMsg
		elif(LogParseAction == 'Ignore'):
			def noMsg(m):
				pass
			msgFcn = noMsg
		else:
			raise ValueError(f"invalid value '{LogParseAction}' for LogParseAction")
		
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
		
		#initialize idx
		idx=-1
		
		for fn in filenames:
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
							msgFcn(f"Start of packet found at line {lc} of {short_name} while in {status} mode")
						
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
								msgFcn(f"Unknown sequence found in preamble at line {lc} of file {short_name} : {repr(line)}")
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
								msgFcn(f"Unknown separator found in preamble at line {lc} of file {short_name} : {repr(line)}")
								#drop back to search mode
								status='searching'
						elif(not line):
							msgFcn('Empty line in preamble at line {lc} of file {short_name}');
						else:
							#split line on colon
							lp=line.split(':')
							#the MATLAB version uses genvarname but we just strip whitespace cause dict doesn't care
							name=lp[0].strip()
							#reconstruct the rest of line
							arg=':'.join(lp[1:])

							#check if key exists in dictionary
							if(name in self.log[idx].keys()):
								msgFcn(f"Duplicate field {name} found at line {lc} of file {short_name}")
							else:
								self.log[idx][name]=arg
								#check for arguments
								if(name=='Arguments'):
									self.log[idx]['_Arguments']=self._argParse(arg)
								
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
								msgFcn(f"Unknown sequence found at line {lc} of file {short_name} : {repr(line)}")
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
									msgFcn('Unknown separator found at line {lc} of file {short_name} : {repr(line)}')
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
								msgFcn(f"Unknown sequence found at line {lc} of file {short_name} : {repr(line)}")
								#drop back to search mode
								status='searching'
							elif(line.startswith('===End')):
								#end of entry, go into search mode
								status='searching'
								#mark entry as complete
								self.log[idx]['complete']=True
							else:
								msgFcn('Unknown separator found at line {lc} of file {short_name} : {repr(line)}')
								#drop back to search mode
								status='searching'
		
		for fn in adnames:
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
		idx=self._logMatch({search_field:search_term})
		
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
				
	def datafilenames(self,ftype='mat'):
		
		types=re.compile(r"\.?(?P<csv>csv)|(?P<mat>mat)|(?P<wav>wav)|(?P<sm_mat>sm(?:all)?_mat)",re.IGNORECASE)
		
		m=types.match(ftype)
		
		if(m.group('mat')):
			tstFiles={'ext':'.mat','path':'data','singular':True}
		elif(m.group('csv')):
			tstFiles={'ext':'.csv','path':'post-processed-data\\csv','singular':False}
		elif(m.group('wav')):
			tstFiles={'ext':'','path':'post-processed-data\\wav','singular':True}
		elif(m.group('sm_mat')):
			tstFiles={'ext':'.mat','path':'post-processed-data\\mat','singular':True}
		else:
			raise RuntimeError(f"'{ftype}' is an invalid file type")
			
		
		fn=[None]*len(self.found)
		for i,idx in enumerate(self.found):
			if(self.log[idx]['operation'] == 'Test'):
				prefix=['capture_']
				folder=[tstFiles['path']]
				ext=tstFiles['ext']
				singular=tstFiles['singular']
			elif(self.log[idx]['operation'] == 'Training'):
				prefix=['Training_']*2
				folder=['training','data']
				ext='.mat'
				singular=True
			elif(self.log[idx]['operation'] == 'Tx Two Loc Test'):
				prefix=['Tx_capture','capture']
				folder=['tx-data']*len(prefix)
				ext='.mat'
				singular=True
			elif(self.log[idx]['operation'] == 'Rx Two Loc Test'):
				prefix=['Rx_capture','capture']
				folder=['rx-data']*len(prefix)
				ext='.mat'
				singular=True
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
				continue

			#get date string in file format
			date_str=self.log[idx]['date'].strftime('%d-%b-%Y_%H-%M-%S')

			for f,p in zip(folder,prefix):

				foldPath=os.path.join(self.searchPath,f)

				filenames=glob.glob(os.path.join(foldPath,p+'*'+ext))

				match=[f for f in filenames if date_str in f ]

				if(not singular and len(match)>=1):
					fn[i]=match
					break
				elif(len(match)>1):
					print(f"More than one file found matching '{date_str}' in '{f}")
					fn[i]='Multiple'
				elif(len(match)==1):
					fn[i]=match[0]
					break
			else:
				if(fn[i] is None):
					warnings.warn(RuntimeWarning(f"No matching files for '{date_str}' in '{foldPath}'"),stacklevel=2)

		return fn

	def findFiles(self,locpath,ftype='mat'):
		network_path = self.searchPath
		
#		self.searchPath = network_path
		net_names = self.datafilenames()
		
		# Identify all sessions marked error on network
		net_errSessions = [name == ":Error" for name in net_names]
		
		# Identify all sessions marked Incomplete on network
		net_incSessions = [name == ":Incomplete" for name in net_names]
		
		# Identify all sessoins that could not be identified on netowkr
		net_notFound = [name == None for name in net_names]
		
		if(any(net_notFound)):
			warnings.warn(RuntimeWarning(f"'{sum(net_notFound)}' files not found on network"),stacklevel=2)
		
		# Switch to searching localpath
		self.searchPath = locpath
		loc_names = self.datafilenames()
		
		# Identify all sessions marked error locally
		loc_errSessions = [name == ":Error" for name in loc_names]
		# Combine all sessions we want to ignore
		tossSessions = [loc_errSessions[i] or net_errSessions[i] or net_incSessions[i] or net_notFound[i] for i in range(0,len(loc_errSessions))]
		
		# Toss unwanted sessions
		loc_names = [loc_names[i] for i in range(0,len(loc_names)) if(not(tossSessions[i]))]
		net_names = [net_names[i] for i in range(0,len(net_names)) if(not(tossSessions[i]))]
		
		# Find remaining files missing locally
		loc_notFound = [name == None for name in loc_names]
		
		if(any(loc_notFound)):
			
			filenames_parts = [os.path.split(x) for x in net_names]
			filenames_elev = [os.path.basename(x[0]) for x in filenames_parts]
			for i in range(0,len(loc_notFound)):
				if(loc_notFound[i]):
					netpath = net_names[i]
					
					localpath = os.path.join(locpath,filenames_elev[i],filenames_parts[i][1])
					print(f"Copying from:\n -- {netpath}")
					print(f"Copying to:\n -- {localpath}")
					shutil.copy2(netpath,localpath)
		
		filenames = self.datafilenames(ftype=ftype)
		filenames = [filenames[i] for i in range(0,len(filenames)) if(not(tossSessions[i]))]
		if(filenames == []):
			raise RuntimeError("Could not find any files meeting search criteria")
		self.searchPath = network_path
		return(filenames)

	def isAncestor(self,rev,repo_path,git_path=None):
		
		if(git_path is None):
			git_path='git'
			
		#dummy name in case it is not used
		tmpdir=None
		try:
			
			if(isGitURL(repo_path)):
				#save URL
				repo_url=repo_path
				#generate temp dir
				tmpdir=tempfile.TemporaryDirectory()
				#print message to inform the user
				print(f"Cloning : {repo_path}")
				#set repo path to temp dir
				repo_path=tmpdir.name
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
			
			hashCache={}
			
			for k,l in enumerate(self.log):
				hash=l['Git Hash'].strip()
				
				if(not hash):
					#skip this one
					continue
				
				#dump dty flag
				hash=hash.split()[0]
				
				if(hash not in hashCache.keys()):
				
					#check that hash is valid
					p=subprocess.run([git_path,'-C',repo_path,'cat-file','-t',hash],capture_output=True)
					
					if(p.returncode):
						warnings.warn(RuntimeWarning(f"Could not get hash for {hash} {p.stderr.decode('utf-8').strip()}"),stacklevel=2)
						#store result in hash cache
						hashCache[hash]=False
						#skip this one
						continue
						
					p=subprocess.run([git_path,'-C',repo_path,'show-branch','--merge-base',rev_p,hash],capture_output=True)
					#remove spaces from base
					base=p.stdout.decode("utf-8").strip()
					#check for errors
					if(p.returncode):
						warnings.warn(RuntimeWarning(f"Could not get the status of log entry {k} git returned : {base}"),stacklevel=2)
						
					hashCache[hash]=(base == rev_p)
				
				if(hashCache[hash]):
					match.append(k)
		finally:
			if(tmpdir):
				#must delete directory manually because of a bug in TemporaryDirectory
				#see https://bugs.python.org/issue26660
				#.git has read only files
				shutil.rmtree(os.path.join(tmpdir.name,'.git'),onerror=del_rw)
				#cleanup dir
				tmpdir.cleanup()
				
				
					
		self._foundUpdate(match)
		
		return match

	def argSearch(self,name,value):
		
		def listCmp(l1,l2):
			
			m=[False]*len(l2)
			
			for a in l1:
				res=[valCmp(a,b) for b in l2]
				
				#make sure that there was a match
				if(not any(res)):
					return False
				
				#OR lists together
				m=[a|b for a,b in zip(m,res)]
			
			return all(m)
				
		
		def valCmp(arg,val):
			if(isinstance(arg,list) and isinstance(val,list)):
				return listCmp(arg,val)
			elif(isinstance(arg,list) and not isinstance(val,list)):
				return listCmp(arg,[val])
			elif((not isinstance(arg,list)) and isinstance(val,list)):
				return listCmp([arg],val)
			elif(isinstance(arg,str)):
				m=re.search(val,arg)
				return not not m
			else:
				return arg==val
		
		match=[]
		for i,l in enumerate(self.log):
			try:
				if(valCmp(l['_Arguments'][name],value)):
					match.append(i)
			except KeyError:
				#argument not found, not a match
				pass
				
		self._foundUpdate(match)
		
		return match

	def _argParse(self,args):
					
		def str_or_float(val):
			if(not val):
				return None
			m=re.match(r"(?P<str>'(?P<s>[^']*)')|(?P<true>true)|(?P<false>false)",val)
			if(m):
				if(m.group('str')):
					return m.group('s')
				elif(m.group('true')):
					return True
				elif(m.group('false')):
					return False
				else:
					raise RuntimeError('Internal Error')
			else:
				try:
					return float(val)
				except ValueError:
					warnings.warn(RuntimeWarning(f"Could not convert '{val}'"),stacklevel=2)
					return val

		match_args=re.finditer(r"'(?P<name>[^']*)',(?P<value>(?P<cell_m>\{(?P<cell>[^}]*)\})|(?P<arr_m>\[(?P<arr>[^]]*)\])|(?:[^{[][^,]*))",args)
		
		#dictionary for args
		arg_d={}
		
		for m in match_args:
			#check for cell array
			if(m.group('cell_m')):
				if(m.group('cell')):
					arg_d[m.group('name')]=[str_or_float(v) for v in re.split(';|,',m.group('cell'))]
				else:
					arg_d[m.group('name')]=[]
			#check for a array
			elif(m.group('arr_m')):
				if(m.group('arr')):
					arg_d[m.group('name')]=[str_or_float(v) for v in re.split(';|,',m.group('arr'))]
				else:
					arg_d[m.group('name')]=[]
			else:
				arg_d[m.group('name')]=str_or_float(m.group('value'))
		
		return arg_d
		
	@property
	def flog(self):
		return [self.log[i] for i in self.found]

		
#workaround for deleting read only files
#code from : https://bugs.python.org/issue19643#msg208662
def del_rw(action, name, exc):
	os.chmod(name, stat.S_IWRITE)
	os.remove(name)

def isGitURL(str):
	if(str.startswith('git@')):
		return True
	elif(str.startswith('https://')):
		return True
	elif(str.startswith('http://')):
		return True
	else:
		return False
