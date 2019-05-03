from log_search import log_search
	
ls=log_search('\\\\cfs2w.nist.gov\\671\\Projects\\MCV\\Access-Time\\')

print(ls.log[-2])