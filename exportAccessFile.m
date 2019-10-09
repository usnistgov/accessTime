function csv_names = exportAccessFile(filename,varargin)
% Input parser
p = inputParser();

% Validation functions
% Determine if x is a valid data directory
isDatDir = @(x) exist(x,'dir') || strcmp(x,'');

% Expansion parameter for reprocessing MRT scores
addParameter(p,'timeExpand',0,@(x) validateattributes(x,{'numeric'},{'scalar','>=',0}));

% Default data directory
default_dat_dir = fullfile('data');
% Where data is stored
addParameter(p,'dat_dir',default_dat_dir, isDatDir);

default_exportExtras = true;
% Flag for exporting wav files of recordings or not
addParameter(p,'exportExtras', default_exportExtras,@(x) validateattributes(x,{'numeric','logical'},{'scalar'}));

% Default folder where mat, csv, and wav files will be saved
default_out_dir = fullfile('post-processed data');
addParameter(p,'out_dir',default_out_dir,isDatDir);

% Add parameter to import an existing mat file or load in required data
% from callers workspace
addParameter(p,'importFile',true,@(x) validateattributes(x,{'numeric','logical'},{'scalar'}));

addRequired(p,'filename');
parse(p,filename,varargin{:});

% Strip extension off of filename
[~,fname] = fileparts(filename);
%% CSV Setup
% Define directories to store csv, mat, and wav files
csvdir = fullfile(p.Results.out_dir,'csv');
% Make the directories as needed
checkdir(csvdir);

% Grab directory structure of csv directory
csvDir = dir(csvdir);
% Names of all csv files currently in folder
current_csv = {csvDir.name};
% See if any of the csv files currently are made from fname base
cnames_ix = contains(current_csv,fname);
if(any(cnames_ix))
    cflag = 1;
    csv_names = current_csv(cnames_ix);
else
    cflag = 0;
end

%% Extra Setup: Wav files and stripped mat file
if(p.Results.exportExtras)
    % Setup directories
    wavdir = fullfile(p.Results.out_dir,'wav');
    matdir = fullfile(p.Results.out_dir,'mat');
    
    checkdir(wavdir);
    checkdir(matdir);
    
    % Check if directories already exist
    wname = fullfile(wavdir,fname);
    if(exist(wname,'dir'))
        wflag = 1;
    else
        wflag = 0;
        mkdir(wname);
    end
    
    if(p.Results.timeExpand)
        timeEx = p.Results.timeExpand*48e3;
        fname_new = strrep(filename,'.mat',['_TE-' num2str(timeEx) '-samples.mat']);
        mname = fullfile(matdir,fname_new);
    else
        mname = fullfile(matdir,filename);
    end
    if(exist(mname,'file'))
        mflag = 1;
    else
        mflag = 0;
    end
    if(wflag && cflag && mflag)
        disp([filename ' --Data already exported...skipping'])
        return;
    end
else
    if(cflag)
        disp([filename '--Data already exported...skipping'])
        return;
    end
end

if(p.Results.importFile)
    % Need to load in a data file
    datpath = fullfile(p.Results.dat_dir, filename);
    % Load data
    disp(['Loading ' datpath])
    dat = load(datpath);
    if(p.Results.timeExpand)
        [~,success] = reprocessMRT(datpath,'timeExpand',p.Results.timeExpand);
        dat.test_dat.success = success;
    end
    
    % Assign required variables
    fs = dat.fs;
    test_dat = dat.test_dat;
    AudioFiles = dat.AudioFiles;
    y = dat.y;
    ptt_st_dly = dat.ptt_st_dly;
    % Delete unnecessary variables
    clear('dat')
else
    % Data does not need to be loaded =>
    % Grab required variables from workspace of caller
    test_dat = evalin('caller', 'test_dat');
    fs = evalin('caller', 'fs');
    AudioFiles = evalin('caller','AudioFiles');
    y = evalin('caller','y');
    ptt_st_dly = evalin('caller','ptt_st_dly');
end
%% CSV File
clip_names = cell(length(AudioFiles),1);
for k = 1:length(AudioFiles)
    [~,clip_names{k}] = fileparts(AudioFiles{k});
end
disp('Exporting csv for each clip')
cname = fullfile(csvdir,fname);
csv_names = cell(length(y),1);
for clip = 1:length(y)
    if(p.Results.timeExpand)
        timeEx = p.Results.timeExpand*48e3;
        csv_names{clip} = [cname '_' clip_names{clip} '_TE-' num2str(timeEx) '-samples.csv'];
    else
        csv_names{clip} = [cname '_' clip_names{clip} '.csv'];
    end
    fid = fopen(csv_names{clip},'w');
    % Write the header
    fprintf(fid,'AudioFiles = %s\n', AudioFiles{clip});
    fprintf(fid, 'fs =  %d\n', fs);
    fprintf(fid,'----------------\n');
    fprintf(fid,'PTT_time,PTT_start,ptt_st_dly,P1_Int,P2_Int,m2e_latency,underRun,overRun\n');
    % Define Data matrix
    datmat = [test_dat.ptt_time(test_dat.clipi == clip);
        test_dat.ptt_start(test_dat.clipi == clip);
        ptt_st_dly{clip}(test_dat.dly_idx(test_dat.clipi == clip));
        test_dat.success(1,test_dat.clipi == clip);
        test_dat.success(2,test_dat.clipi == clip);
        test_dat.dly_its(test_dat.clipi == clip);
        test_dat.underRun(test_dat.clipi == clip);
        test_dat.overRun(test_dat.clipi == clip);
        ];
    % Write the data
    fprintf(fid,'%d,%d,%d,%d,%d,%d,%d,%d\n', datmat);
    fclose(fid);
end
%% Extra Files
if(p.Results.exportExtras)
    %% Wav files
    disp('Exporting Wav Files')
    for k = 1:length(test_dat.recordings)
        if(mod(k,length(test_dat.recordings)/10) == 0)
            disp(['Rx ' num2str(k) '/' num2str(length(test_dat.recordings))])
        end
        rname = ['Rx' num2str(k) '_' clip_names{test_dat.clipi(k)} '.wav'];
        rec = test_dat.recordings{k}(:,1);
        audiowrite(fullfile(wname,rname),rec,fs)
    end
    
    %% Stripped mat file
    rmVars = {'recordings'};
    test_dat = rmfield(test_dat,rmVars);
    
    saveVars = {'test_dat';
        'y';
        'fs';
        'AudioFiles';
        'ptt_st_dly';};
    
    disp(['-----Saving reduced test info file ' mname])
    save(mname,saveVars{:});
    
end


end

function eFlag = checkdir(path)
eFlag = exist(path,'dir');
if(~eFlag)
    mkdir(path);
end
end