function filenames = findFiles(log,local_searchpath,network_searchpath)
%%  Function to find files from a log search locally or on a network drive
% 
% FINDFIlES(log, local_searchpath, network_searchpath) Searches for the log
% files denoted by log.found in the local search path. If the files are not
% found it then searches the network search path. Any files found on the
% network search path are copied over to the local search path. 

log.searchPath = local_searchpath;
filenames = log.datafilenames()';

% Drop any error sessions that were found
errSessions = cellfun(@(x) strcmp(':Error',x),filenames);
filenames = filenames(~errSessions);

notFound = cellfun(@isempty, filenames);

if(any(notFound))
    % Find it on the network and copy
    log.searchPath = network_searchpath;
    filenames_net = log.datafilenames()';
    errSessions = cellfun(@(x) strcmp(':Error',x),filenames_net);
        if(any(errSessions))
            warning([num2str(sum(errSessions)) ' files had errors'])
            filenames_net = filenames_net(~errSessions);
            filenames = filenames(~errSessions);
            notFound = notFound(~errSessions);
        end
    notFound_net = cellfun(@isempty,filenames_net);
    if(all(notFound == notFound_net))
        warning([num2str(sum(notFound_net)) ' files not found on network'])
        filenames = filenames(~notFound);
    else
        filenames_net = filenames_net(~notFound_net);
        notFound = notFound(~notFound_net);
        
        % Some files on network that aren't local => copy them
        filenames_parts = cellfun(@(x) strsplit(x,'\'),filenames_net,'UniformOutput',0);
        % Reorganize into single cell array
        fileparts = vertcat(filenames_parts{:});
        
        for k = 1:size(fileparts,1)
            if(notFound(k))
                netpath = filenames_net{k};
                localpath = fullfile('..',fileparts{k,end-1}, fileparts{k,end});
                fprintf('Copying from:\n --%s\n', netpath);
                fprintf('Copying to:\n --%s\n', localpath);
                
                [status,msg,msgID] = copyfile(netpath,localpath);
                if(~status)
                    error([msg '. ' msgID])
                end
            end
        end
        
        %     filenames = log2filenames(log(idx),local_searchpath)';
        log.searchPath = local_searchpath;
        filenames = log.datafilenames();
    end
elseif(isempty(filenames))
    error('Could not find any grant files that satisfy parameters')
end

end