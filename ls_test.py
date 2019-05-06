from log_search import log_search
import re

def testSearch(ls,test):
	print(f"searching with '{repr(test)}'")
	print(ls.MfSearch(test))


ls=log_search('\\\\cfs2w.nist.gov\\671\\Projects\\MCV\\Access-Time\\')

print(ls.log[-2])
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
#find files
print(f"datafilenames returned : {ls.datafilenames()}")