from log_search import log_search
	
ls=log_search('\\\\cfs2w.nist.gov\\671\\Projects\\MCV\\Access-Time\\')

print(ls.log[-2])
#run a search
ls.MfSearch({'operation':'Test','System':' Direct'})
#clear found
ls.clear()
#run another search
print(ls.MfSearch({'operation':'Test','Rx Device':' 3506'}))