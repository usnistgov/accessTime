function test(varargin)

%TEST run a access time test
%
%	test() runs a access time test
%
%	TEST(name,value) same as above but specify test parameters as name
%	value pairs. Possible name value pairs are shown below
%
%   NAME                TYPE                DESCRIPTION
%   
%   AudioFile           char vector         Audio file to use for test. The
%                           or              cutpoints for the file must
%                       cell array          exist in the same directory
%                                           with the same name with a .csv
%                                           extension. If a cell array is
%                                           given then the test is run in
%                                           succession for each file in the
%                                           array.
%
%   Trials              positive int        Number of trials to run at a
%                                           time. Test will run the number
%                                           of trials given by Trials
%                                           before pausing for user input.
%                                           This allows for battery changes
%                                           or radio cooling if needed. If
%                                           pausing is not desired set
%                                           Trials to Inf.
%
%   RadioPort           char vector,string  Port to use for radio
%                                           interface. Defaults to the
%                                           first port where a radio
%                                           interface is detected.
%
%	PTTDelay			double				PTTDelay can be a 1 or 2
%                                           element double vector. If it is
%                                           a 1 element vector then it
%                                           specifies the minimum PTT delay
%                                           that will be used with the
%                                           maximum being the end of the
%                                           first word in the clip. If a
%                                           two element vector then the
%                                           first element is the smallest
%                                           delay used and the second is
%                                           the largest. Defaults to zero
%                                           (start of clip).
%
%	PTTStep				double				Time in seconds between
%                                           successive PTT delays. Default
%                                           20 ms.
%
%   BGNoiseFile         char vector         If this is non empty then it is
%                                           used to read in a noise file to
%                                           be mixed with the test audio.
%                                           Default is no background noise.
%
%   BGNoiseVolume       double              Scale factor for background
%                                           noise. Defaults to 0.1.
%
%	PTTGap				double				Time to pause after completing
%                                           one trial and starting the
%                                           next. Defaults to 3.1 s. 
%
%	OutDir				char vector			Directory that is added to the
%                                           output path for all files.
%
%	PTTrep				positive int		Number of times to repeat a
%                                           given PTT delay value. If
%                                           autoStop is used PTTrep must be
%                                           greater than 15.
%
%	autoStop			logical				Enable checking for access and
%                                           stopping the test when it is
%                                           detected.
%
%	StopRep				positive int		Number of times that access
%                                           must be detected in a row
%                                           before the test is completed.
%
%	DevDly				double				Delay in seconds of the audio
%                                           path with no communication
%                                           device present. Defaults to
%                                           21e-3.
%
%	DataFile			char vector			Name of a temporary datafile to
%                                           use to restart a test. If this
%                                           is given all other parameters
%                                           are ignored and the settings
%                                           that the original test was
%                                           given are used.
%
%   TimeExpand          numeric             Length of time, in seconds, of
%                                           extra audio to send to
%                                           ABC-MRT16. Adding time protects
%                                           against inaccurate M2E latency
%                                           calculations and misaligned
%                                           audio. A scalar value sets time
%                                           expand before and after the
%                                           keyword. A two element vector
%                                           sets the time at the begining
%                                           and the end seperatly.
%
%   SThresh             numeric             The threshold of A-weight power
%                                           for P2, in dB, below which a
%                                           trial is considered to have no
%                                           audio. Defaults to -50
%
%
%   STries              numeric             Number of times to retry the
%                                           test before giving up. defaults
%                                           to 3
%
%   RetryFunc           function_handle     Function to call when STries
%                                           has been exceeded
%
%   PTTnum              numeric             Number of the PTT output to
%                                           use. Defaults to 1.
%    


%This software was developed by employees of the National Institute of
%Standards and Technology (NIST), an agency of the Federal Government.
%Pursuant to title 17 United States Code Section 105, works of NIST
%employees are not subject to copyright protection in the United States and
%are considered to be in the public domain. Permission to freely use, copy,
%modify, and distribute this software and its documentation without fee is
%hereby granted, provided that this notice and disclaimer of warranty
%appears in all copies.
%
%THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND, EITHER
%EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY
%WARRANTY THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED
%WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
%FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION WILL
%CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE ERROR
%FREE. IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING, BUT NOT
%LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES, ARISING
%OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS SOFTWARE,
%WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR OTHERWISE, WHETHER
%OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY OR OTHERWISE, AND
%WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT OF THE RESULTS OF, OR
%USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.


%% ========================[Parse Input Arguments]========================

%create new input parser
p=inputParser();

%add optional filename parameter
addParameter(p,'AudioFile','test.wav',@validateAudioFiles);
%add number of trials parameter
addParameter(p,'Trials',100,@(t)validateattributes(t,{'numeric'},{'scalar','positive'}));
%add radio port parameter
addParameter(p,'RadioPort','',@(n)validateattributes(n,{'char','string'},{'scalartext'}));
%add ptt delay parameter
addParameter(p,'PTTDelay',0,@validate_delay);
%add ptt step parameter
addParameter(p,'PTTStep',20e-3,@(n)validateattributes(n,{'numeric'},{'scalar','nonempty','positive'}));
%add background noise file parameter
addParameter(p,'BGNoiseFile','',@(n)validateattributes(n,{'char'},{'scalartext'}));
%add background noise volume parameter
addParameter(p,'BGNoiseVolume',0.1,@(n)validateattributes(n,{'numeric'},{'scalar','nonempty','nonnegative'}));
%add ptt gap parameter
addParameter(p,'PTTGap',3.1,@(t)validateattributes(t,{'numeric'},{'scalar','nonnegative'}));
%add output directory parameter
addParameter(p,'OutDir','',@(n)validateattributes(n,{'char'},{'scalartext'}));
%add PTT repetition parameter
addParameter(p,'PTTrep',30,@(t)validateattributes(t,{'numeric'},{'scalar','integer','positive'}));
%add stopping condition parameter
addParameter(p,'autoStop',true ,@(t) validateattributes(t,{'logical','numeric'},{'scalar'}))
%add stop condition repetitions parameter
addParameter(p,'StopRep',10,@(t)validateattributes(t,{'numeric'},{'scalar','integer','positive'}));
%add device latency parameter
addParameter(p,'DevDly',21e-3,@(t)validateattributes(t,{'numeric'},{'scalar','positive'}));
%add partial datafile parameter
addParameter(p,'DataFile',[],@(d)validateattributes(d,{'char','string'},{'scalartext'}));
% add parameter to reprocess MRT with bigger windows
addParameter(p,'TimeExpand',[],@validate_expand);
% add A-weight silence threshold parameter
addParameter(p,'SThresh',-50,@(t)validateattributes(t,{'numeric'},{'scalar'}));
%add silence threshold tries parameter
addParameter(p,'STries',3,@(t)validateattributes(t,{'numeric'},{'scalar','integer','positive'}));
%add error function parameter
addParameter(p,'RetryFunc',[],@validate_func);
%add PTT output number parameter
addParameter(p,'PTTnum',1,@(t)validateattributes(t,{'numeric'},{'scalar','integer','positive'}));



%parse inputs
parse(p,varargin{:});

%% =====================[Check inter argument values]=====================

if(p.Results.autoStop && p.Results.PTTrep<15)
    error('PTTrep must be greater than 15 if autoStop is used');
end

%% ======================[List Vars to save in file]======================
%This is a list of all the files to save in data files. This is don both
%for a normal test run and if an error is encountered. This list is here so
%there is only one place to add new variables that need to be saved in the
%file

save_vars={'git_status','y','dev_name','ptt_st_dly','cutpoints','bad_name',...
           'fs','test_info','p','AudioFiles','temp_data_filenames','wavdir',...
        ...%save pre test notes, post test notes will be appended later
           'pre_notes'};

%% ===================[load in old data file if given]===================

if(~isempty(p.Results.DataFile))
    %save filename for error message
    dfile=p.Results.DataFile;
    %load in new datafile, overwrites input arguments
    load(dfile,save_vars{:},'post_notes');
    %set file status to resume so we skip some things
    file_status='resume';
    
    trialCount=0;
    
    %array of files to copy to new names
    copy_files=zeros(1,length(temp_data_filenames),'logical');             %#ok loaded from file
    %save old names to copy to new names
    old_filenames=temp_data_filenames;
    %save old .wav folder
    old_wavdir=wavdir;                                                     %#ok loaded from file
    %save old bad file
    old_bad_name=bad_name;                                                 %#ok loaded from file
    
    for k=1:length(temp_data_filenames)
        save_dat=load_dat(temp_data_filenames{k});
        if(isempty(save_dat))
            fprintf('No data file found for ''%s''\n',temp_data_filenames{k});
        else
            %file is good, need to copy to new name
            copy_files(k)=true;
            %get number of rows
            clen=height(save_dat);
            %initialize success with zeros
            success=zeros(2,length(ptt_st_dly{k})*p.Results.PTTrep);       %#ok loaded from file
            %fill in success from file
            success(1,1:clen)=save_dat.P1_Int;
            success(2,1:clen)=save_dat.P2_Int;
            %stop flag is computed every delay step
            stopFlag=NaN(1,length(ptt_st_dly{k}));
            %trial count is the sum of all trial counts from each file
            trialCount=trialCount+clen;
            %set clip start to current index
            %if another datafile is found it will be overwritten
            clip_start=k;
            %set clip count from number of rows in file
            clip_count=clen;
            %initialize k_start
            k_start=1;
            %loop through data and evaluate stop condition
            for kk=p.Results.PTTrep:p.Results.PTTrep:clen

                % Identify trials calculated at last timestep
                ts_ix = (kk-(p.Results.PTTrep-1)):kk;
                stopFlag(k_start)= checkStopCondition(success(:,1:kk),ts_ix);
                
                k_start=k_start+1;
            end
            
            if(clen==0)
                kk_start=1;
            else
                %remainder goes to kk_start
                kk_start=mod(clen-1,p.Results.PTTrep)+2;
            end

        end
        
    end
else
    %set file status to 
    file_status='init';
    %set initial loop indices
    clip_start=1;
    k_start=1;
    kk_start=1;
end
       
%% ===================[Read in Audio file(s) for test]===================
   
%only need to read in data if this is the first time
if(strcmp(file_status,'init'))
    %check if audio file is a cell array
    if(iscell(p.Results.AudioFile))
        %yes, copy
        AudioFiles=p.Results.AudioFile;
    else
        %no, create cell array
        AudioFiles={p.Results.AudioFile};
    end

    %cell array of audio clips to use
    y=cell(size(AudioFiles));
    cutpoints=cell(size(AudioFiles));

    %sample audio sample rate to use
    fs=48e3;

    %check if a noise file was given
    if(~isempty(p.Results.BGNoiseFile))
        %read background noise file
        [nf,nfs]=audioread(p.Results.BGNoiseFile);
        %check if sample rates match
        if(nfs~=fs)
            %calculate resample factors
            [prs,qrs]=rat(fs/nfs);
            %resample if necessary
            nf=resample(nf,prs,qrs);
        end
    end

    %read in audio files and perform checks
    for k=1:length(AudioFiles)
        %read audio file
        [y{k},fs_file]=audioread(AudioFiles{k});

        %check fs and resample if necessary
        %TODO : determine what to do about cut points
        if(fs_file~=fs)
            %calculate resample factors
            [prs,qrs]=rat(fs/fs_file);
            %resample to 48e3
            y{k}=resample(y{k},prs,qrs);
        end

        %reshape y to be a column vector/matrix
        y{k}=reshape(y{k},sort(size(y{k}),'descend'));

        %check if there is more than one channel
        if(size(y{k},2)>1)
            %warn user
            warning('audio file has %i channels. discarding all but channel 1',size(y,2));
            %get first column
            y{k}=y{k}(:,1);
        end

        %split file into parts
        [path,name,~]=fileparts(AudioFiles{k});

        %create cutpoints name
        cutname=fullfile(path,[name '.csv']);

        %check if file exists
        if(~exist(cutname,'file'))
            error('Could not find cutpoint file')
        end

        %read in cutpoints file
        cutpoints{k}=read_cp(cutname);

        %check file
        if(size(cutpoints{k},1)~=4)
            error('loading ''%s'' : 4 "words" expected but, %i found',AudioFiles{k},size(cutpoints{k},1));
        end

        if(~isnan(cutpoints{k}(1,1)) || ~isnan(cutpoints{k}(3,1)))
            error('loading ''%s'' : Words 1 and 3 must be silence',AudioFiles{k})
        end

        if(cutpoints{k}(2,1)~=cutpoints{k}(4,1))
            error('loading ''%s'' : Words 2 and 4 must be the same',AudioFiles{k})
        end

        %check if we need to add noise
        if(~isempty(p.Results.BGNoiseFile))
            %extend noise file to match y
            nfr=repmat(nf,ceil(length(y{k})/length(nf)),1);   
            %add noise file to sample
            y{k}=y{k}+p.Results.BGNoiseVolume*nfr(1:length(y{k}));
        end    
    end
end
%% =======================[Compare inter word delay]=======================

T=cellfun(@(c)diff(c(3,2:3)),cutpoints)/fs;

%check if all delays are the same
if(length(unique(T))>1)
    %give warning
    warning('It is recommended that all inter word times are the same')
end

%% =========================[Compute expand time]=========================

if(isempty(p.Results.TimeExpand))
    %set time expand to give extra space at the begining
    TimeExpand=[100e-3 - 0.11e-3,0.11e-3];
else
    exlen=length(p.Results.TimeExpand);
    if(exlen==1)
        %set symetric time expand
        TimeExpand=[1,1]*p.Results.TimeExpand;
    elseif(exlen==2)
        %set time expand from parm
        TimeExpand=reshape(p.Results.TimeExpand,1,[]);
    else
        error('internal error setting TimeExpand');
    end
end

%% ========================[Setup Playback Object]========================

%create an object for playback and recording
aPR=audioPlayerRecorder(fs);

%set bit depth
aPR.BitDepth='24-bit integer';

%chose which device to use
dev_name=choose_device(aPR);

%set input channel mapping
aPR.RecorderChannelMapping=[1,2];
    
%set output channel mapping
aPR.PlayerChannelMapping=[1,2];

%print the device used
fprintf('Using "%s" for audio test\n',dev_name);

%% ===========================[Read git status]===========================

%get git status
stat=gitStatus();

%first time, just set to git_status 
if(strcmp(file_status,'init'))
    %get git status
    git_status=stat;
else
    %if we have already restarted this datafile then git_status is a cell
    if(iscell(git_status))                                                  %#ok read from data file
        %append to the list
        git_status{end+1}=stat;
    else
        %create cell array with git stats
        git_status={git_status,stat};
    end
    %check git status against the original
    if(~git_status_check(git_status{1},git_status{end}))
        %different git versions give warning, failure is likely
        warning('Restarting test with different git version than original')
    end
end

%% ==================[Initialize file and folder names]==================

%folder name for data
dat_fold=fullfile(p.Results.OutDir,'data');

%folder name for recovery data
recovery_fold=fullfile(dat_fold,'recovery');

%folder name for error data
error_fold = fullfile(dat_fold,'error');

%folder name for plots
plots_fold=fullfile(p.Results.OutDir,'plots');

%file name for log file
log_name=fullfile(p.Results.OutDir,'tests.log');

%file name for test type
test_name=fullfile(p.Results.OutDir,'test-type.txt');

%directory to save csv files
csvdir=fullfile(dat_fold,'csv');

%make csv directory
[~,~,~]=mkdir(csvdir);

%make plots directory
[~,~,~]=mkdir(plots_fold);

%make recovery directory
[~,~,~]=mkdir(recovery_fold);

%make error directory
[~,~,~,] = mkdir(error_fold);

%% =========================[Get Test Start Time]=========================

%get start time
dt_start=datetime('now','Format','dd-MMM-yyyy_HH-mm-ss');
%get a string to represent the current date in the filename
dtn=char(dt_start);

%format for clip timestamps (has ms)
clip_timestamp_format='dd-MMM-yyyy_HH-mm-ss.SSS';

%initialize clip end time for gap time calculation
time_e=NaT;

%% ==================[Get Test info and notes from user]==================

%if this is the first time read from test-type file
if(strcmp(file_status,'init'))
    %open test type file
    init_tstinfo=readTestState(test_name);
else
    %use the one from data file
    init_tstinfo=test_info;                                                 %#ok loaded from file
end

%width for a device prompt
dev_w=20;
%initialize prompt array
prompt={};
%initialize text box dimensions array
dims=[];
%initialize empty response array
resp={};

%add test type prompt to dialog
prompt{end+1}='Test Type';
dims(end+1,:)=[1,50];
resp{end+1}=init_tstinfo.testType;
%add Tx radio ID prompt to dialog
prompt{end+1}='Transmit Device';
dims(end+1,:)=[1,dev_w];
resp{end+1}=init_tstinfo.TxDevice;
%add Rx radio ID prompt to dialog
prompt{end+1}='Receive Device';
dims(end+1,:)=[1,dev_w];
resp{end+1}=init_tstinfo.RxDevice;
%add radio system under test prompt
prompt{end+1}='System';
dims(end+1,:)=[1,60];
resp{end+1}=init_tstinfo.System;
%add test notes prompt
prompt{end+1}='Please enter notes on test conditions';
dims(end+1,:)=[15,100];

%check if this is a restart
if(strcmp(file_status,'init'))
    %use empty test notes
    resp{end+1}='';
else
    notes=strtrim(pre_notes);                                               %#ok pre_notes loaded from file
    %if not empty add newline
    if(~isempty(notes))
        notes=[notes newline];
    end
    %use notes from file and add note of error
    notes=[notes 'Test Restarted due to error' newline...
        'Data loaded from : ' dfile newline...
        sprintf('Restarting at trial #%d\n',trialCount)];                  
    
    %check if post notes were written to file
    if(exist('post_notes','var'))
        %trim notes
        p_notes=strtrim(post_notes);
        %check if they exist
        if(~isempty(p_notes))
            %add with newline between
            notes=[notes newline sprintf('Post test notes from %s :\n',dfile) p_notes];
        end
    end
        %split filename to construct error file
        [fold,ename,eExt]=fileparts(dfile);

        %construct error filename
        eload_name=fullfile(fold,[ename '_ERROR' eExt]);

        %check if error file exists
        if(exist(eload_name,'file'))
            %only load post_notes
            load(eload_name,'post_notes');
            %trim notes
            p_notes=strtrim(post_notes);
            %check if they exist
            if(~isempty(p_notes))
                %add with newline between
                notes=[notes sprintf('Post test notes from %s :\n',eload_name) p_notes];
            end
        end
    
    %add notes to field value
    resp{end+1}=notes;
end

%dummy struct for sys_info
test_info=struct('testType','');

%loop while we have an empty test type
while(isempty(test_info.testType))
    %prompt the user for test info
    resp=inputdlg(prompt,'Test Info',dims,resp);
    %check if anything was returned
    if(isempty(resp))
        %exit program
        return;
    else
        %get test state from dialog
        test_info=getTestState(prompt(1:(end-1)),resp(1:(end-1)));
        %write test state
        writeTestState(test_name,test_info);
    end
    %check if a test type was given
    if(~isempty(test_info.testType))
        %print out test type
        fprintf('Test type : %s\n',test_info.testType);
        %preappend underscore and trim whitespace
        test_type_str=['_',strtrim(test_info.testType)];
        %test_type_str set, loop will now exit
    end
end
%% ===============[Print Log entry so it is easily copyable]===============

%get notes from response
pre_note_array=resp{end};

%get strings from output add newlines only
pre_note_strings=cellfun(@(s)[s,newline],cellstr(pre_note_array),'UniformOutput',false);
%get a single string from response
pre_notes=horzcat(pre_note_strings{:});

%print
fprintf('Pre test notes:\n%s\n',pre_notes);


%% ========================[Open Radio Interface]========================
%radio interface oppened here so that we can add version to the log
ri=radioInterface(p.Results.RadioPort);

%% ===============[Parse User response and write log entry]===============

%get strings from output add a tabs and newlines
pre_note_tab_strings=cellfun(@(s)[char(9),s,newline],cellstr(pre_note_array),'UniformOutput',false);
%get a single string from response
pre_notesT=horzcat(pre_note_tab_strings{:});

if(iscell(git_status))
    gstat=git_status{1};
else
    gstat=git_status;
end

%check dirty status
if(gstat.Dirty)
    %local edits, flag as dirty
    gitdty=' dty';
else
    %no edits, don't flag
    gitdty='';
end

%get call stack info to extract current filename
[ST, I] = dbstack('-completenames');
%get current filename parts
[~,n,e]=fileparts(ST(I).file);
%full name of current file without path
fullname=[n e];

%open log file
logf=fopen(log_name,'a+');
%set time format of start time
dt_start.Format='dd-MMM-yyyy HH:mm:ss';
%write start time, test type and git hash
fprintf(logf,['\n>>Test started at %s\n'...
              '\tTest Type  : %s\n'...
              '\tGit Hash   : %s%s\n'...
              '\tfilename   : %s\n'],char(dt_start),test_info.testType,gstat.Hash,gitdty,fullname);
%write Tx device ID
fprintf(logf, '\tTx Device  : %s\n',test_info.TxDevice);
%write Rx device ID
fprintf(logf, '\tRx Device  : %s\n',test_info.RxDevice);
%write system under test 
fprintf(logf, '\tSystem     : %s\n',test_info.System);
%write system under test 
fprintf(logf, '\tArguments     : %s\n',extractArgs(p,ST(I).file));
%write system under test 
fprintf(logf, '\tRIversion     : %s\n',ri.getVersion());
%write system under test 
fprintf(logf, '\tRI ID         : %s\n',ri.getID());
%write pre test notes
fprintf(logf,'===Pre-Test Notes===\n%s',pre_notesT);
%close log file
fclose(logf);

%% =======================[Filenames for data files]=======================

%generate base file name to use for all files
base_filename=sprintf('capture%s_%s',test_type_str,dtn);

%generate filename for .wav files
wavdir=fullfile(dat_fold,'wav',base_filename);

%create wav directory
[~,~,~]=mkdir(wavdir);

%get name of audio clip without path or extension
[~,clip_names,~]=cellfun(@fileparts,AudioFiles,'UniformOutput',false);

%get name of csv files with path and extension
data_filenames = fullfile(csvdir,cellfun(@(cn)sprintf('%s_%s.csv',base_filename,cn),clip_names,'UniformOutput',false));

%get name of temp csv files with path and extension
temp_data_filenames = fullfile(csvdir,cellfun(@(cn)sprintf('%s_%s_TEMP.csv',base_filename,cn),clip_names,'UniformOutput',false));

%generate filename for error data
error_filename=fullfile(error_fold,sprintf('%s_ERROR.mat',base_filename));

%generate filename for temporary data
temp_filename=fullfile(recovery_fold,sprintf('%s_TEMP.mat',base_filename));

%filename to hold the location of last temp file
temp_filename_filename=fullfile(p.Results.OutDir,'tempName.txt');

%generate filename for bad data
bad_name=fullfile(csvdir,sprintf('%s_BAD.csv',base_filename));

%% ======================[Copy files To new filname]======================
if(strcmp(file_status,'resume'))
    for k=1:length(old_filenames)
        if(copy_files(k))
            copyfile(old_filenames{k},temp_data_filenames{k});
        end
    end
    copyfile(old_wavdir,wavdir);
    %copy bad file if it exists
    if(exist(old_bad_name,'file'))
        copyfile(old_bad_name,bad_name);
    end
end
%% ======================[Generate oncleanup object]======================

%add cleanup function
co=onCleanup(@()cleanFun(error_filename,data_filenames,temp_filename,log_name));
    
%% =====================[Generate filters and times]=====================

%calculate niquest frequency
fn=fs/2;

%create lowpass filter for PTT signal processing
ptt_filt=fir1(400,200/fn,'low');

%generate time vector for y
t_y=cellfun(@(v)(1:length(v))/fs,y,'UniformOutput',false);

%% ====================[Resample Factors for ITS_delay]====================

%sample rate for ITS delay
fs_ITS_dly=8e3;

%calculate resample factors
[p_ITS_dly,q_ITS_dly]=rat(fs_ITS_dly/fs);

%% ======================[Write transmit audio files]======================

for k=1:length(AudioFiles)
    wav_name = sprintf('Tx_%s',clip_names{k});
    audiowrite(fullfile(wavdir,[wav_name '.wav']),y{k},fs)

    %open cutpoints file file
    f=fopen(fullfile(wavdir,[wav_name '.csv']),'w');
    %write header
    fprintf(f,'Clip,Start,End\n');
    %write data
    fprintf(f,'%d,%d,%d\n',cutpoints{k}');
    %close file
    fclose(f);

end

%% ========================[Create ABC MRT object]========================

MRT_obj=ABC_MRT16();

%% ========================[Notify user of start]========================

%turn on LED when test starts
ri.led(1,true);

try
    
    %% ====================[check if init is required]====================
     %only preallocate if this is a new file
    if(strcmp(file_status,'init'))

        %% =====================[Generate PTT delays]=====================

        %preallocate
        ptt_st_dly=cell(1,length(cutpoints));

        %push to talk delay for each trial
        if(length(p.Results.PTTDelay)==1)
            %generate delays for each clip
            for k=1:length(cutpoints)
                %word end time from end of word
                w_end=(cutpoints{k}(2,3)/fs);
                %word start time from end of first silence
                w_st=(cutpoints{k}(1,3)/fs);
                %delay during word
                w_dly=w_st:p.Results.PTTStep:w_end;
                %delay during silence
                s_dly=w_st:-p.Results.PTTStep:(p.Results.PTTDelay);
                %generate delay from word delay and silence delay
                %word delay must be reversed
                ptt_st_dly{k}=[w_dly(end:-1:1) s_dly(2:end)];
            end
        else
            ptt_st_dly(:)={(p.Results.PTTDelay(2)):-p.Results.PTTStep:(p.Results.PTTDelay(1))};
        end

        %% =====================[initialize variables]=====================
        
        %running count of the number of completed trials
        trialCount=0;

    %% =======================[End of optional Init]======================

    end

    %% ==========================[Save Temp file]==========================

    %save all data and post notes
    save(temp_filename,save_vars{:},'-v7.3');
    %print out file location
    fprintf('Temporary file saved in ''%s''\n',temp_filename);
    %open file for temp name
    ftn=fopen(temp_filename_filename,'w');
    
    if(ftn==-1)
        warning('Unable to open temp filename file for writing');
    else
        fprintf(ftn,'%s\n',temp_filename);
        fclose(ftn);
    end
    
    %% =====================[Save time for set timing]====================

    set_start=tic();
    
    %% ============================[Clip loop]============================
    
    for clip=clip_start:length(AudioFiles)
        %% ==================[Calculate Delay Start Idx]==================
        %calculate index to start M2E latency at. This is 3/4 through the
        %second silence. if more of the clip is used ITS_delay can get
        %confused and return bad values
        
        dly_st_idx = round(cutpoints{clip}(3,2) + 0.75*diff(cutpoints{clip}(3,2:3)));
                
        %% =========[check if file is not present (not a restart)]=========
        if(~exist(temp_data_filenames{clip},'file'))
            
            %% =====================[write CSV header]=====================

            csvf=fopen(temp_data_filenames{clip},'w');
            % Write the header
            fprintf(csvf,'AudioFiles = %s\n', AudioFiles{clip});
            fprintf(csvf, 'fs =  %d\n', fs);
            fprintf(csvf,'----------------\n');
            fprintf(csvf,'PTT_time,PTT_start,ptt_st_dly,P1_Int,P2_Int,m2e_latency,underRun,overRun,TimeStart,TimeEnd,TimeGap\n');
            fclose(csvf);


            %print name and location of datafile
            fprintf('Starting %s\nStoring data in:\n\t''%s''\n',clip_names{clip},temp_data_filenames{clip});

            %% ========================[Stop Flag]========================

            success=zeros(2,length(ptt_st_dly)*p.Results.PTTrep);

            %stop flag is computed every delay step
            stopFlag=NaN(1,length(ptt_st_dly{clip}));

            %initialize clip count
            clip_count=0;
        end

        %% =======================[Delay Step Loop]=======================

        for k=k_start:length(ptt_st_dly{clip})
            
            %% ===============[Print Current Clip and Delay]==============
            fprintf('Delay : %f s\nClip : %s\n',ptt_st_dly{clip}(k),clip_names{clip});
            
            %%  =====================[Measurement Loop]====================
            
            for kk=kk_start:p.Results.PTTrep
                
                %% ================[Increment Trial Count]================

                trialCount=trialCount+1;

                %% ================[Increment Clip Count]================
                
                clip_count=clip_count+1;

                %% =======================[Check loop]=====================
                
                %A-weight power of P2, used for silence detection
                a_p2=-inf;
                %number of retries for clip
                retries=0;
                
                while(~(a_p2>p.Results.SThresh))
                    
                    retries=retries+1;                        
                    
                    %check if we have lots of retries
                    if(retries>p.Results.STries)
                        %turn on LED when waiting for user input
                        ri.led(2,true);
                        %inform user of problem
                        fprintf('Audio not detected through the system.');
                        %check if we have retry function
                        if(~isempty(p.Results.RetryFunc))
                            %number of times function has been called on
                            %this clip
                            num_call=(retries-1)-p.Results.STries;
                            %print message to user
                            fprintf('Attempting automatic restart\n');
                            %call function, if it returns nonzero test will
                            %wait for user input
                            user_pause=p.Results.RetryFunc(num_call,trialCount,clip_count);
                        else
                            user_pause=true;
                        end
                        %check if pause is needed
                        if(user_pause)
                            fprintf(' Check connections and radios and press enter to continue.\n');
                            beep;beep;
                            %wait for input
                            pause;
                        end
                        
                        %turn off LED, resuming
                        ri.led(2,false);
                    end
                    
                    %%  ============[Key Radio and Play Audio]============

                    %setup the push to talk to trigger
                    ri.ptt_delay(ptt_st_dly{clip}(k),p.Results.PTTnum,'UseSignal',true);

                    %save end time of prevous clip
                    time_last=time_e;
                    
                    %get start timestamp
                    time_s=datetime('now','Format',clip_timestamp_format);
                    
                    %play and record audio data
                    [dat,underRun,overRun]...
                        =play_record(aPR,y{clip},'OverPlay',1,'StartSig',true);

                    %get start time
                    time_e=datetime('now','Format',clip_timestamp_format);

                    %get the wait state from radio interface
                    state=ri.WaitState;

                    %un-push the push to talk button
                    ri.ptt(false,p.Results.PTTnum);

                    %check wait state to see if PTT was triggered properly
                    switch(state)
                        case 'Idle'
                            %everything is good, do nothing
                        case 'Signal Wait'
                            %still waiting for start signal, give error
                            error('Radio interface did not receive the start signal. Check connections and output levels')
                        case 'Delay'
                            %still waiting for delay time to expire, give warning
                            warning('PTT delay longer than clip')
                        otherwise
                            %unknown state
                            error('Unknown radio interface wait state ''%s''',state)
                    end
                    
                    %calculate gap time
                    time_gap=time_s-time_last;
                    %set format to get ms
                    time_gap.Format='hh:mm:ss.SSS';

                    %%  ===============[pause between runs]===============
                    pause(p.Results.PTTGap);

                    %%  =================[Data Processing]=================

                    %extract push to talk signal (getting envelope)
                    ptt_sig=filtfilt(ptt_filt,1,abs(dat(:,2)));

                    %get aximum value
                    ptt_max=max(ptt_sig);

                    %check levels
                    if(ptt_max<0.25)
                        warning('Low PTT signal values. Check levels');
                    end

                    %normalize levels
                    ptt_sig=ptt_sig*sqrt(2)/ptt_max;

                    % of ensuring ptt_start (low priority)
                    ptt_st_idx=find(ptt_sig>0.5,1);

                    if(isempty(ptt_st_idx))
                        st=NaN;
                        figure('Name',sprintf('Missing PTT File %i step %i rep %i',clip,k,kk));
                        plot(ptt_sig);
                    else
                        % Convert sample index to time
                        st=ptt_st_idx/fs;
                    end

                    %find when the ptt was pushed
                    ptt_start=st;

                    %get ptt time. subtract nominal play/record delay
                    ptt_time=ptt_start-p.Results.DevDly;

                    %calculate delay. Only use data after dly_st_idx
                    tmp=1/fs_ITS_dly*ITS_delay_wrapper(...
                        resample(y{clip}(dly_st_idx:end,1)',p_ITS_dly,q_ITS_dly),...
                        resample(dat(dly_st_idx:end,1),p_ITS_dly,q_ITS_dly),...
                        'f','dlyBounds',[0,Inf]);
                    
                    %get delay from results
                    dly_its=tmp(2);

                    %interpolate for new time
                    rec_int=griddedInterpolant((1:length(dat(:,1)))/fs-dly_its,dat(:,1));

                    %new shifted version of signal
                    rec_a=rec_int(t_y{clip});

                    %expand cutpoints by TimeExpand
                    ex_cp=round(cutpoints{clip}([2,4],[2,3]) -  (TimeExpand*fs).*[1,-1]);

                    %limit cutpoints to clip length
                    ylen=length(y{clip});
                    ex_cp(ex_cp>ylen)=ylen;

                    %minimum cutpoint index is 1
                    ex_cp(ex_cp<1)=1;

                    %split file into clips
                    dec_sp={rec_a(ex_cp(1,1):ex_cp(1,2))',rec_a(ex_cp(2,1):ex_cp(2,2))'};

                    %compute MRT scores for clips
                    [~,success(:,clip_count)]=...
                        MRT_obj.process(dec_sp,cutpoints{clip}([2 4],1));

                    %%  ============[Calculate A-weight of P2]============

                    a_p2=A_weighted_power(dec_sp{2},fs);
                    
                    if(~(a_p2>p.Results.SThresh))
                        warning('A-weight power for P2 is %.2f dB',a_p2);
                        
                        %save bad audio file
                        wav_name = sprintf('Bad%d_r%u_%s.wav',clip_count,retries,clip_names{clip});
                        audiowrite(fullfile(wavdir,wav_name),dat,fs);
                        
                        %print message
                        fprintf('Saving bad data to ''%s''\n',bad_name);
                        %check if file exists
                        if(exist(bad_name,'file'))
                            %file exists, append
                            badf=fopen(bad_name,'a');
                        else
                            %file does not exist open for writing
                            badf=fopen(bad_name,'w');
                            %write header
                            fprintf(badf,'FileName,trialCount,clipCount,try#,p2A-weight,m2e_latency,underRun,overRun,TimeStart,TimeEnd,TimeGap\n');
                        end
                        %write bad data to file
                        fprintf(badf,'%s,%u,%u,%u,%g,%g,%u,%u,%s,%s,%s\n',...
                            wav_name,trialCount,clip_count,retries,a_p2,...
                            dly_its,underRun,overRun,...
                            char(time_s),char(time_e),char(time_gap));
                        
                        %close bad file
                        fclose(badf);
                    end
                    
                %%  ===================[End Check loop]===================
                
                end
                
                %%  ===============[Inform User of Restart]===============
                
                %check if it took more than one try
                if(retries>1)
                    %print message that test is continuing
                    fprintf('A-weight power of %.2f dB for P2. Continuing test\n',a_p2);
                end

                %%  ================[Save Trial Data]===============
                
                csvf=fopen(temp_data_filenames{clip},'a');
                fprintf(csvf,'%g,%g,%g,%g,%g,%g,%u,%u,%s,%s,%s\n',...
                    ptt_time,ptt_start,ptt_st_dly{clip}(k),...
                    success(1,clip_count),success(2,clip_count),...
                    dly_its,underRun,overRun,...
                    char(time_s),char(time_e),char(time_gap)...
                    );
                fclose(csvf);
                
                %save audio file
                wav_name = sprintf('Rx%d_%s.wav',clip_count,clip_names{clip});
                audiowrite(fullfile(wavdir,wav_name),dat,fs)

                
                %%  ==================[Check Trial Limit]=================

                if(mod(trialCount,p.Results.Trials)==0)
                    %print message to user
                    %calculate set time
                    set_time=seconds(toc(set_start));
                    %set format
                    set_time.Format='hh:mm:ss';
                    
                    %print set time
                    fprintf('Time for %i trials : %s\n',p.Results.Trials,char(set_time));
                    
                    %turn on LED when waiting for user input
                    ri.led(2,true);

                    fprintf('Trial Limit reached. Check Batteries and press enter to continue\n');
                    %beep to alert the user
                    beep;
                    %pause to wait for user
                    pause;
                    
                    %turn off LED, resuming
                    ri.led(2,false);
                    
                    %save time for next set
                    set_start=tic();
                end

            %%  ===================[End Measurement Loop]==================

            end
            
            %reset start index to so we start at the beginning
            kk_start=1;
            
            %%  ===============[Check stopping condition]==================
            
            % Identify trials calculated at last timestep ptt_st_dly(k)
            ts_ix = (clip_count-(p.Results.PTTrep-1)):clip_count;
            % Compute if stopping criteria met
            stopFlag(k) = checkStopCondition(success(:,1:clip_count),ts_ix);

            %check if we should look for stopping condition
            %only stop if ptt delay is before the first word
            if(p.Results.autoStop && (cutpoints{clip}(1,3)/fs)>ptt_st_dly{clip}(k))
                if(p.Results.StopRep<k &&  all(stopFlag((k-p.Results.StopRep+1):k)))
                    % If stopping condition met, break from loop
                    break;
                end
            end
            
        %%  =====================[End Delay Step Loop]====================

        end

        %reset start index to so we start at the beginning
        k_start=1;
        
    %% ==========================[End Clip Loop]=========================
    
    end
    
    %%  ===================[Change Name of data files]====================
    
    for k=1:length(temp_data_filenames)
        fprintf('Renaming ''%s'' to ''%s''\n',temp_data_filenames{k},data_filenames{k});
        movefile(temp_data_filenames{k},data_filenames{k});
    end
    
    %%  ========================[save datafile]=========================
    
    %change file status to complete
    file_status='complete';                                                %#ok saved in datafile

    %check if there is a temporary data file
    if(exist(temp_filename,'file'))
        fprintf('Deleting Temporary file ''%s''\n',temp_filename);
        %delete temporary data file
        delete(temp_filename);
    end
    
    %% ========================[Zip Audio Files]=========================
    
    fprintf('Compressing audio files\n');
    
    %files to compress
    comp_glob='Rx*.wav';
    
    %list files
    wav_dir_files=cellstr(ls(fullfile(wavdir,comp_glob)));
    
    zip(fullfile(wavdir,'audio.zip'),wav_dir_files,wavdir);
    
    %delete audio dir
    fprintf('Deleting compressed audio\n');
    %first remove .wav files
    delete(fullfile(wavdir,comp_glob));
    
%%  ===========================[Catch Errors]===========================
catch err
    %add error to dialog prompt
    dlgp=sprintf(['Error Encountered with test:\n'...
                  '"%s"\n'...
                  'Please enter notes on test conditions'],...
                  strtrim(err.message));
    
    %get error test notes
    resp=inputdlg(dlgp,'Test Error Conditions',[15,100]);

    %open log file
    logf=fopen(log_name,'a+');

    %check if dialog was not canceled
    if(~isempty(resp))
        %get notes from response
        post_note_array=resp{1};
        %get strings from output add a tabs and newlines
        post_note_tab_strings=cellfun(@(s)[char(9),s,newline],cellstr(post_note_array),'UniformOutput',false);
        %get a single string from response
        post_notesT=horzcat(post_note_tab_strings{:});
        %get strings from output add newlines only
        post_note_strings=cellfun(@(s)[s,newline],cellstr(post_note_array),'UniformOutput',false);
        %get a single string from response
        post_notes=horzcat(post_note_strings{:});

        %write start time to file with notes
        fprintf(logf,'===Test-Error Notes===\n%s',post_notesT);
    else
        %dummy var so we can save
        post_notes='';
    end
    %print end of test marker
    fprintf(logf,'===End Test===\n\n');
    %close log file
    fclose(logf);
    
    %set file status to error
    file_status='error';
    
    %start at true
    all_exist=true;
    
    %look at all vars to see if they exist
    for kj=1:length(save_vars)
        if(~exist(save_vars{kj},'var'))
            %all vars don't exist
            all_exist=false;
            %exit loop
            break;
        end
    end
    
    %check that all vars exist
    if(all_exist)
        %save all data and post notes
        save(error_filename,save_vars{:},'err','post_notes','-v7.3');
        %print out file location
        fprintf('Data saved in ''%s''\n',error_filename);
    else
        %save error post notes and file status
        save(error_filename,'err','post_notes','file_status','-v7.3');
        %print out file location
        fprintf('Dummy data saved in ''%s''\n',error_filename);
    end
    
    %check if there is a temporary data file
    if(exist(temp_filename,'file'))
        %append error and post notes to temp file
        save(temp_filename,'err','post_notes','-append');
        %print out temp file name to make restarts easier
        fprintf('\nTemp file name : ''%s''\n\n',temp_filename);
    end
        
    
    %rethrow error
    rethrow(err);
end

%% ===========================[Close Hardware]===========================

%turn off LED when test stops
ri.led(1,false);

%close radio interface
delete(ri);

%% ======================[Check for buffer issues]======================

%check for buffer over runs
if(any(overRun))
    fprintf('There were %i buffer over runs\n',sum(overRun));
else
    fprintf('There were no buffer over runs\n');
end

%check for buffer over runs
if(any(underRun))
    fprintf('There were %i buffer under runs\n',sum(underRun));
else
    fprintf('There were no buffer under runs\n');
end

%% ===========================[Generate Plots]===========================

figure;

colors=lines(length(AudioFiles));

hold on;

for k=1:length(clip_names)
    %load in file
    
    save_dat=load_dat(data_filenames{k});
    
    ptt_time=save_dat.PTT_time;
    
    %plot second word in clip
    scatter(ptt_time,save_dat.P2_Int,'o','MarkerEdgeColor',colors(k,:),...
        'DisplayName',sprintf('%s Second Word',clip_names{k}));
    %plot first word in clip
    scatter(ptt_time,save_dat.P1_Int,'+','MarkerEdgeColor',colors(k,:),...
        'DisplayName',sprintf('%s First Word',clip_names{k}));
end
hold off;

l=legend('Show');

set(l,'Interpreter', 'none');

xlabel('PTT start')
ylabel('Intelligibility');

%% =========================[Beep to alert user]=========================

beep;
pause(1);
beep;

%% ==========================[Cleanup Function]==========================
%This is called when cleanup object co is deleted (Function exits for any
%reason other than CTRL-C). This ensures that the log entries are propperly
%closed and that there is a chance to add notes on what went wrong.

function cleanFun(err_name,good_names,temp_name,log_name)
%check if error .m file exists
if(~exist(err_name,'file'))

    prompt='Please enter notes on test conditions';
    
    good_exist=cellfun(@(gn)exist(gn,'file'),good_names);
    temp_exist=exist(temp_name,'file');
    
    %check to see if data file is missing
    if(all(~good_exist) && ~temp_exist)
        %add not to say that this was an error
        prompt=[prompt,newline,'Complete dataset not found, something went wrong'];
        %set flag
        no_file=true;
    else
        %clear flag
        no_file=false;
    end
    
    %get post test notes
    resp=inputdlg(prompt,'Test Conditions',[15,100]);

    %open log file
    logf=fopen(log_name,'a+');

    %check if dialog was canceled
    if(~isempty(resp))
        %get notes from response
        post_note_array=resp{1};
        %get strings from output add a tabs and newlines
        post_note_tab_strings=cellfun(@(s)[char(9),s,newline],cellstr(post_note_array),'UniformOutput',false);
        %get a single string from response
        post_notesT=horzcat(post_note_tab_strings{:});
        
        %get strings from output add newlines only
        post_note_strings=cellfun(@(s)[s,newline],cellstr(post_note_array),'UniformOutput',false);
        %get a single string from response
        post_notes=horzcat(post_note_strings{:});

        if(no_file)
            %write error notes header
            fprintf(logf,'===Test-Error Notes===\n%s',post_notesT);
        else
            %write post notes header
            fprintf(logf,'===Post-Test Notes===\n%s',post_notesT);
        end
    else
        post_notes=''; 
    end
    %print end of test marker
    fprintf(logf,'===End Test===\n\n');
    %close log file
    fclose(logf);
    
    %check to see if temp data file exists
    if(exist(temp_name,'file'))
        %append post notes to .mat file
        save(temp_name,'post_notes','-append');
    end
end
%% =====================[Stopping Condition function]=====================
function stopFlag = checkStopCondition(success, ts_ix)
% success: array of MRT success values for all trials for the current clip
% ts_ix: indices of trials from latest timestep

% p-value threshold: Threshold for accepting observed value or not. The
% higher alpha is the "stricter" our stopping criteria is. 
alpha = 0.05;

% Isolate scores for p1 and p2 (first and second play of the word)
% % p1 only care about success results from trials at last timestep
p1_success = success(1,ts_ix);
% % p2 care about all trials so far for given clip
p2_success = success(2,:);

% Observed statistic
observed = mean(p2_success) - mean(p1_success);

% Number of trials in population 1
m = length(p1_success);
% Number of trials in population 2
K = length(p2_success);

% Total number of trials between populations
n = m + K;
combo = [p1_success, p2_success];
% Number of resamples to perform
R = 10000;
% Initialize difference array
diffs = zeros(R,1);
for k = 1:R
    % Create random permutation for resampling
    permIx = randperm(n);
    % Grab first m elements of random order for population 1
    p1 = combo(permIx(1:m));
    % Grab remaining K elements of random order for population 2
    p2 = combo(permIx((m+1):end));
    
    % Compute resample statistic (difference of means)
    diffs(k) = mean(p2) - mean(p1);
end

% Calculate p-value for likelihood that observed came from mixed
% distribution
pval = sum(diffs >= observed)/R;

% If pval is greater than alpha 
if(pval >= alpha)
    stopFlag = true;
else
    stopFlag = false;
end
%% =====================[Argument validating functions]=====================
%some arguments require more complex validation than validateattributes can
%provide

function validateAudioFiles(fl)
    validateStr=@(n)validateattributes(n,{'char'},{'vector','nonempty'});
    %check if input is a cell array
    if(iscell(fl))
        %validate each element in the array
        cellfun(validateStr,fl);
    else
        %otherwise validate a single string
        validateStr(fl);
    end

function validate_delay(d)
    validateattributes(d,{'numeric'},{'vector','nonnegative','increasing'});
    %check if length is greater than two
    if(length(d)>2)
        error('Delay must be a one or two element vector.');
    end
    
function validate_expand(t)
    if(~isempty(t))
        validateattributes(t,{'numeric'},{'nonnegative'})
    end
    %check if length is greater than two
    if(length(t)>2)
        error('Time Expand value must be empty or a one or two element vector.');
    end
    
function validate_func(f)
    if(~isempty(f))
        validateattributes(f,{'function_handle'},{'scalar'})
    end
