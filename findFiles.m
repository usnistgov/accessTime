function filenames = findFiles(log,local_searchpath,network_searchpath)
%%  Function to find files from a log search locally or on a network drive
% 
% FINDFIlES(log, local_searchpath, network_searchpath) Searches for the log
% files denoted by log.found in the local search path. If the files are not
% found it then searches the network search path. Any files found on the
% network search path are copied over to the local search path. 

    %save search path
    sp=log.searchPath;

    %set search path
    log.searchPath=network_searchpath;

    %call function
    filenames=log.findFiles(local_searchpath,pyargs('ftype','mat'));

    %restore search path
    log.searchPath=sp;

end