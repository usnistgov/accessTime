from log_search import log_search
import re

def testSearch(ls,test):
	print(f"searching with '{repr(test)}'")
	print(repr(ls.MfSearch(test))+'\n')

def printDatafiles(ls):
	print(f"datafilenames returned :")
	print(repr(ls.datafilenames())+"\n")

print('Opening log:')
ls=log_search('\\\\cfs2w.nist.gov\\671\\Projects\\MCV\\Access-Time\\')

print(f"\n\nLog opened!\nExample entry :\n{ls.log[-2]}\n")
#run a search
testSearch(ls,{'operation':'Test','System':' Direct'})
#clear found
ls.clear()
#run another search
testSearch(ls,{'operation':'Test','Rx Device':' 3506'})
#test string search
testSearch(ls,{'Arguments':'test.wav'})
#test regexp search
testSearch(ls,{'post_notes':r'Optimal volume = [+-]?[0-9]+\.[0-9]+ dB'})
#test flog
print(f"flog : {repr(ls.flog)}")
#test isAncestor
hash='e29daa8dba5fe2e0ed0f5808064234261ad8ce41'
anc=ls.isAncestor(hash,'https://gitlab.nist.gov/gitlab/PSCR/MCV/access-time.git')
print(f"Ancestors of {hash} : {anc}\n")
#find files
printDatafiles(ls)

args=ls.argSearch('PTTrep',30);
print(f"argSearch for PTTrep == 30 : {args}")

clipname = ['F1_b39_w4_hook.wav','F3_b15_w5_west.wav','M4_b18_w4_pay.wav','M3_b22_w3_cop.wav']
args=ls.argSearch('AudioFile',clipname)
print(f"argSearch for AudioFiles : {args}")
printDatafiles(ls)
