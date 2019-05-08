function filenames = findFiles(log,local_searchpath,network_searchpath)
%%  Function to find files from a log search locally or on a network drive
% 
% FINDFIlES(log, local_searchpath, network_searchpath) Searches for the log
% files denoted by log.found in the local search path. If the files are not
% found it then searches the network search path. Any files found on the
% network search path are copied over to the local search path. 

log.searchPath = local_searchpath;
loc_names = log.datafilenames()';

% Identify all sessions identified locally that were marked error
loc_errSessions = cellfun(@(x) strcmp(':Error',x),loc_names);

log.searchPath = network_searchpath;
net_names = log.datafilenames()';
% Idenfity all sessions on network marked error
net_errSessions = cellfun(@(x) strcmp(':Error',x),net_names);

% Identify all sessions on network marked Incomplete
net_incSessions = cellfun(@(x) strcmp(':Incomplete',x),net_names);

% Identify all sessions that could not be identified on network
net_notFound = cellfun(@isempty, net_names);
if(any(net_notFound))
    warning([num2str(sum(net_notFound)) ' files not found on network']);
end

% Total error sessions are either local or net
tossSessions = loc_errSessions | net_errSessions | net_notFound | net_incSessions;

% Toss errSessions
loc_names = loc_names(~tossSessions);
net_names = net_names(~tossSessions);

% Find remaining files missing locally
loc_notFound = cellfun(@isempty, loc_names);

if(any(loc_notFound))
    % Some files on network that aren't local => copy them
    filenames_parts = cellfun(@(x) strsplit(x,'\'),net_names,'UniformOutput',0);
    % Reorganize into single cell array
    fileparts = vertcat(filenames_parts{:});
    
    for k = 1:size(fileparts,1)
        if(loc_notFound(k))
            netpath = net_names{k};
            
            localpath = fullfile('..', fileparts{k,end-1}, fileparts{k,end});
            fprintf('Copying from:\n --%s\n', netpath);
            fprintf('Copying to:\n --%s\n', localpath);
            
            [status,msg,msgID] = copyfile(netpath,localpath);
            if(~status)
                error([msg '. ' msgID])
            end
        end
    end
end

log.searchPath = local_searchpath;
filenames = log.datafilenames()';
filenames = filenames(~tossSessions);

if(isempty(filenames))
    error('Could not find any files meeting search criteria')
end
end