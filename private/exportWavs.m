function exportWavs(sesh,sesh_name,path)
sesh_name = strrep(sesh_name,'.mat','');

tdat_flag = isfield(sesh,'test_dat');

if(~exist(fullfile(path,sesh_name),'dir'))
    % Folder with session files doesn't exist
    % Make it
    mkdir(fullfile(path,sesh_name))
    % sampling rate
    fs = sesh.fs;
    
    if(tdat_flag)
        % number of recordings in file
        nRecs = length(sesh.test_dat.recordings);
    else
        nRecs = length(sesh.recordings);
    end
    
    for i = 1:nRecs
       % File name to be stored
       filename = ['Rx' num2str(i) '.wav'];
       
       if(tdat_flag)
           rec = sesh.test_dat.recordings{i}(:,1);
       else
           rec = sesh.recordings{i}(:,1);
       end
       % Save wav file of just received voice
       audiowrite(fullfile(path,sesh_name,filename),rec,fs);
    end
else
    % Throw warning if folder already exists and exit function
    warning(['Folder ' fullfile(path,sesh_name) ' already exists. Skipping export...'])
end


