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
%	SaveTrials			double				Number of trials to run before
%                                           saving a temporary file. The
%                                           temporary file can be used to
%                                           restart the test where it left
%                                           off. If SaveTrials is zero
%                                           (default) then Trials is used.
%                                           If SaveTrials is Inf no saving
%                                           is done.
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
%	ExtraRadioEn		logical				If true then a 3rd radio is
%                                           keyed after the primary radio
%                                           is keyed.
%
%	ExtraRadioTime		double				Time in seconds to key the 3rd
%                                           radio for.
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
%	TimeExpand			double				Time in seconds to expand the
%                                           cut points by when passing
%                                           audio to ABC MRT16. If NaN is
%                                           given then 1/2 of the time
%                                           between words is used. Default
%                                           is NaN.
%
%	exportExtras		logical				Export .wav and stripped down
%                                           .mat files. Stripped .mat files
%                                           do not contain the recordings
%                                           variable, but have all other
%                                           test data.


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
%add the number of trials between saving temp files
addParameter(p,'SaveTrials',0,@(t)validateattributes(t,{'numeric'},{'scalar','nonnegative'}));
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
addParameter(p,'PTTGap',3.1,@validate_delay);
%add extra radio enable parameter
addParameter(p,'ExtraRadioEN',false,@(t)validateattributes(t,{'numeric','logical'},{'scalar'}));
%add extra radio time parameter
addParameter(p,'ExtraRadioTime',5,@validate_delay);
%add output directory parameter
addParameter(p,'OutDir','',@(n)validateattributes(n,{'char'},{'scalartext'}));
%add PTT repetition parameter
addParameter(p,'PTTrep',15,@(t)validateattributes(t,{'numeric'},{'scalar','integer','positive'}));
%add stopping condition parameter
addParameter(p,'autoStop',false ,@(t) validateattributes(t,{'logical','numeric'},{'scalar'}))
%add stop condition repetitions parameter
addParameter(p,'StopRep',3,@(t)validateattributes(t,{'numeric'},{'scalar','integer','positive'}));
%add device latency parameter
addParameter(p,'DevDly',21e-3,@(t)validateattributes(t,{'numeric'},{'scalar','positive'}));
%add partial datafile parameter
addParameter(p,'DataFile',[],@(d)validateattributes(d,{'char','string'},{'scalartext'}));
% add parameter to reprocess MRT with bigger windows
addParameter(p,'TimeExpand',NaN,@(t)validateattributes(t,{'numeric'},{'scalar','nonnegative'}));
% add parameter to export wav and stripped down mat files
addParameter(p,'exportExtras',false,@(t)validateattributes(t,{'numeric','logical'},{'scalar'}));


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

save_vars={'git_status','y','dev_name','test_dat','ptt_st_dly','cutpoints',...
           'fs','test_info','p','AudioFiles','stopFlag','file_status',...
        ...%save pre test notes, post test notes will be appended later
           'pre_notes'};
     
%for partial data files there are extra vars that must be saved. These are
%not in the final datafile.
partial_vars={'trialCount','clip','k','kk'};


%% ===================[load in old data file if given]===================

if(~isempty(p.Results.DataFile))
    %save filename for error message
    dfile=p.Results.DataFile;
    %load in new datafile, overwrites input arguments
    load(dfile,save_vars{:},partial_vars{:});
    %check file_status from saved file
    if(~strcmp(file_status,'partial'))                                      %#ok read from file
        error('File ''%s'' is not a partial save file. can not resume.',dfile);
    end
    %set file status to resume so we skip some things
    file_status='resume';
    %set initial loop indices from file. do this here so loops in init code
    %don't corrupt them
    clip_start=clip;                                                        %#ok loaded from file
    k_start=k;                                                              %#ok loaded from file
    %can't fully explain why we need to increment kk_start but I think it's
    %because the file is saved inside the loop before the counter is
    %incremented
    kk_start=kk+1;                                                          %#ok loaded from file
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
        cutpoints{k}=csvread(cutname,1,0);

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

if(isnan(p.Results.TimeExpand))
    %set time expand to half of inter word time
    TimeExpand=min(T)/2;
else
    %set time expand from parm
    TimeExpand=p.Results.TimeExpand;
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

%folder name for plots
plots_fold=fullfile(p.Results.OutDir,'plots');

%file name for log file
log_name=fullfile(p.Results.OutDir,'tests.log');

%file name for test type
test_name=fullfile(p.Results.OutDir,'test-type.txt');

%make plots directory
[~,~,~]=mkdir(plots_fold);

%make data directory
[~,~,~]=mkdir(dat_fold);

%% ===========================[Set Save Trials]===========================

%read from arguments
SaveTrials=p.Results.SaveTrials;

%check if zero
if(SaveTrials==0)
    %read from trials
    SaveTrials=p.Results.Trials;
end

%% =========================[Get Test Start Time]=========================

%get start time
dt_start=datetime('now','Format','dd-MMM-yyyy_HH-mm-ss');
%get a string to represent the current date in the filename
dtn=char(dt_start);

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
%check if we have a 3rd device
if(p.Results.ExtraRadioEN)
    %add 3rd radio ID prompt to dialog
    prompt{end+1}='Third Device';
    dims(end+1,:)=[1,dev_w];
    resp{end+1}=init_tstinfo.ThirdDevice;
end
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
        sprintf('Restarting at trial #%d\n',trialCount)];                   %#ok trialCount loaded from file
    
    %check if post notes were written to file
    if(exist('post_notes','var'))
        %trim notes
        p_notes=strtrim(post_notes);                                        %#ok post_notes loaded from file
        %check if they exist
        if(~isempty(p_notes))
            %add with newline between
            notes=[notes newline p_notes];
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
                notes=[notes newline p_notes];
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

%% ===============[Parse User response and write log entry]===============

%get notes from response
pre_note_array=resp{end};
%get strings from output add a tabs and newlines
pre_note_tab_strings=cellfun(@(s)[char(9),s,newline],cellstr(pre_note_array),'UniformOutput',false);
%get a single string from response
pre_notesT=horzcat(pre_note_tab_strings{:});

%get strings from output add newlines only
pre_note_strings=cellfun(@(s)[s,newline],cellstr(pre_note_array),'UniformOutput',false);
%get a single string from response
pre_notes=horzcat(pre_note_strings{:});                                     %#ok saved in file

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
%check if we have a 3rd device
if(p.Results.ExtraRadioEN)
    %write 3rd device ID
    fprintf(logf, '\t3rd Device : %s\n',test_info.ThirdDevice);
end
%write system under test 
fprintf(logf, '\tSystem     : %s\n',test_info.System);
%write system under test 
fprintf(logf, '\tArguments     : %s\n',extractArgs(p,ST(I).file));
%write pre test notes
fprintf(logf,'===Pre-Test Notes===\n%s',pre_notesT);
%close log file
fclose(logf);

%% =======================[Filenames for data files]=======================

%generate base file name to use for all files
base_filename=sprintf('capture%s_%s',test_type_str,dtn);

%generate filename for good data
data_filename=fullfile(dat_fold,sprintf('%s.mat',base_filename));

%generate filename for error data
error_filename=fullfile(dat_fold,sprintf('%s_ERROR.mat',base_filename));

%generate filename for temporary data
temp_filename=fullfile(dat_fold,sprintf('%s_TEMP.mat',base_filename));

%% ======================[Generate oncleanup object]======================

%add cleanup function
co=onCleanup(@()cleanFun(error_filename,data_filename,temp_filename,log_name));
    
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

%% ========================[Open Radio Interface]========================

ri=radioInterface(p.Results.RadioPort);

%% ========================[Create ABC MRT object]========================

MRT_obj=ABC_MRT16();

%% ========================[Notify user of start]========================

%print name and location of run
fprintf('Storing data in:\n\t''%s''\n',fullfile(dat_fold,sprintf('%s.mat',base_filename)));

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

        %% =====================[Calculate Max Trials]=====================

        maxTrials=sum(cellfun(@length,ptt_st_dly)*p.Results.PTTrep);

        %% ======================[preallocate arrays]======================
        %give arrays dummy values so things go faster and mlint doesn't
        %complain
    
        %test data struct, holds data from all trials
        test_dat=struct();

        %number of buffer under runs for each trial as returned by play_record
        test_dat.underRun=zeros(1,maxTrials);
        %number of buffer over runs for each trial as returned by play_record
        test_dat.overRun=zeros(1,maxTrials);
        %cell array of recordings for each trial as returned by play_record
        test_dat.recordings=cell(1,maxTrials);
        %delay for each trial
        test_dat.dly_its=zeros(1,maxTrials);
        %start time of the PTT signal as detected from CH2 in the recording
        test_dat.ptt_start=zeros(1,maxTrials);
        %actual delay that the uC used
        test_dat.ptt_uC_dly=zeros(1,maxTrials);
        %adjusted PTT start time for device latency
        test_dat.ptt_time=zeros(1,maxTrials);
        %MRT results for each trial
        test_dat.success=zeros(2,maxTrials);
        %index of delay for trial
        test_dat.dly_idx=zeros(1,maxTrials);
        %This is for the case of multiple audio clips used in a test
        %zeros for now, will be filled in during test
        test_dat.clipi=zeros(1,maxTrials);
        %running count of the number of completed trials
        trialCount=0;
    
        %% ==========================[Stop Flag]==========================
        %stop flag is computed every trial, not every trial so size is
        %different because it is not in the test_dat structure it will not
        %be resized so, it is initialized to NaN's so it is apparent which
        %ones were evaluated

        %results from checkStopCondition for each trial
        stopFlag=NaN(length(AudioFiles),max(cellfun(@length,ptt_st_dly)));

        %% =================[Initialize extra radio times]=================

        if(p.Results.ExtraRadioEN)
            %check if between pause runs is random
            if(length(p.Results.ExtraRadioTime)==1)
                %set all to the same value
                test_dat.extra_radio_time=ones(1,maxTrials)*p.Results.ExtraRadioTime;
            else
                %generate random delays
                test_dat.extra_radio_time=p.Results.ExtraRadioTime(1)+diff(p.Results.ExtraRadioTime)*rand(1,maxTrials);
            end
        else
            test_dat.extra_radio_time=[];
        end

        %% ===================[Initialize PTT gap time]===================

        %check if between pause runs is random
        if(length(p.Results.PTTGap)==1)
            %set all to the same value
            test_dat.ptt_gap_act=ones(1,maxTrials)*p.Results.PTTGap;
        else
            %generate random delays
            test_dat.ptt_gap_act=p.Results.PTTGap(1)+diff(p.Results.PTTGap)*rand(1,maxTrials);
        end
    %% =======================[End of optional Init]======================

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
        
        %% =======================[Delay Step Loop]=======================

        for k=k_start:length(ptt_st_dly{clip})
            
            %% ===============[Print Current Clip and Delay]==============
            [~,name,~]=fileparts(AudioFiles{clip});
            fprintf('Delay : %f s\nClip : %s\n',ptt_st_dly{clip}(k),name);
        
            %%  =====================[Measurement Loop]====================
            
            for kk=kk_start:p.Results.PTTrep
                
                %% ================[Increment Trial Count]================

                trialCount=trialCount+1;

                %% ===================[Set clip index]====================

                test_dat.clipi(trialCount)=clip;
                
                %% ===================[Set delay index]====================
                
                test_dat.dly_idx(trialCount)=k;

                %%  ==============[Key Radio and Play Audio]==============

                %setup the push to talk to trigger
                test_dat.ptt_uC_dly(trialCount)=...                                              
                    ri.ptt_delay(ptt_st_dly{clip}(k),1,'UseSignal',true);

                %play and record audio data
                [dat,test_dat.underRun(trialCount),test_dat.overRun(trialCount)]...
                    =play_record(aPR,y{clip},'OverPlay',1,'StartSig',true);

                %get the wait state from radio interface
                state=ri.WaitState;

                %un-push the push to talk button
                ri.ptt(false,1);

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

                %%  =================[pause between runs]=================
                pause(test_dat.ptt_gap_act(trialCount));

                %%  ===================[Data Processing]===================

                %save data
                test_dat.recordings{trialCount}=dat;

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
                    figure('Name',sprintf('Missing PTT run %i',trialCount));
                    plot(ptt_sig);
                else
                    % Convert sample index to time
                    st=ptt_st_idx/fs;
                end

                %find when the ptt was pushed
                test_dat.ptt_start(trialCount)=st;

                %get ptt time. subtract nominal play/record delay
                test_dat.ptt_time(trialCount)=...
                    test_dat.ptt_start(trialCount)-p.Results.DevDly;

                %calculate delay. Only use data after dly_st_idx
                tmp=1/fs_ITS_dly*ITS_delay_wrapper(...
                    resample(y{clip}(dly_st_idx:end,1)',p_ITS_dly,q_ITS_dly),...
                    resample(dat(dly_st_idx:end,1),p_ITS_dly,q_ITS_dly),...
                    'f');

                %get delay from results
                test_dat.dly_its(trialCount)=tmp(2);

                %interpolate for new time
                rec_int=griddedInterpolant((1:length(dat(:,1)))/fs-test_dat.dly_its(trialCount),dat(:,1));

                %new shifted version of signal
                rec_a=rec_int(t_y{clip});
                
                %expand cutpoints by TimeExpand
                ex_cp=round(cutpoints{clip}([2,4],[2,3]) -  TimeExpand*fs*[1,-1]);
                
                %limit cutpoints to clip length
                ylen=length(y{clip});
                ex_cp(ex_cp>ylen)=ylen;
                
                %minimum cutpoint index is 1
                ex_cp(ex_cp<1)=1;
                
                %split file into clips
                dec_sp={rec_a(ex_cp(1,1):ex_cp(1,2))',rec_a(ex_cp(2,1):ex_cp(2,2))'};

                %compute MRT scores for clips
                [~,test_dat.success(:,trialCount)]=...
                    MRT_obj.process(dec_sp,cutpoints{clip}([2 4],1));


                %%  ====================[Key 3rd radio]====================

                %check if we should key up the extra radio
                if(p.Results.ExtraRadioEN)

                    %push the push to talk button
                    ri.ptt(true,2);
                    %wait for dummy call time
                    pause(test_dat.extra_radio_time(trialCount));
                    %un-push the push to talk button
                    ri.ptt(false,2);
                    %pause between runs
                    pause(test_dat.ptt_gap_act(trialCount));
                end
                %%  ================[Check Save Trial Limit]===============
                
                if(mod(trialCount,SaveTrials)==0)
                    %change file status to partial
                    file_status='partial';                                  %#ok saved in file

                    fprintf('Saving partial data file in ''%s''.\n',temp_filename);
                    %save partial data file
                    save(temp_filename,save_vars{:},partial_vars{:},'-v7.3');

                end
                
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
            
            % Identify all trials performed for current clip
            clipIx = test_dat.clipi == clip;
            % Identify trials calculated at last timestep ptt_st_dly(k)
            ts_ix = test_dat.dly_idx==k & clipIx;
            % Compute if stopping criteria met
            stopFlag(clip,k) = checkStopCondition(test_dat.success,clipIx,ts_ix);

            if(p.Results.autoStop)    
                if(p.Results.StopRep<k &&  all(stopFlag(clip,(k-p.Results.StopRep+1):k)))
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
    
    %% ==========================[Resize Arrays]=========================
    
    for v=fieldnames(test_dat)'
        %only resize nonempty fields
        if(~isempty(test_dat.(v{1})))
            test_dat.(v{1})=test_dat.(v{1})(:,1:trialCount);
        end
    end
    
    %%  ========================[save datafile]=========================
    
    %change file status to complete
    file_status='complete';                                                %#ok saved in datafile
    
    save(data_filename,save_vars{:},'-v7.3');
    
    %check if there is a temporary data file
    if(exist(temp_filename,'file'))
        fprintf('Deleting Temporary file ''%s''\n',temp_filename);
        %delete temporary data file
        delete(temp_filename);
    end
    
    %%  ========================[save csv file]=========================
    
    exportAccessFile(fullfile(p.Results.OutDir,[base_filename '.mat']),...
        'exportExtras',p.Results.exportExtras,...
        'importFile',false);
    
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
if(any(test_dat.overRun))
    fprintf('There were %i buffer over runs\n',sum(test_dat.overRun));
else
    fprintf('There were no buffer over runs\n');
end

%check for buffer over runs
if(any(test_dat.underRun))
    fprintf('There were %i buffer under runs\n',sum(test_dat.underRun));
else
    fprintf('There were no buffer under runs\n');
end

%% ===========================[Generate Plots]===========================

figure;

colors=lines(length(AudioFiles));

hold on;
for k=1:length(AudioFiles)
    [~,name,~]=fileparts(AudioFiles{k});
    %plot second word in clip
    scatter(test_dat.ptt_start(k==test_dat.clipi),...
        test_dat.success(2,k==test_dat.clipi),'o',...
        'MarkerEdgeColor',colors(k,:),...
        'DisplayName',sprintf('%s Second Word',name));
    %plot first word in clip
    scatter(test_dat.ptt_start(k==test_dat.clipi),...
        test_dat.success(1,k==test_dat.clipi),'+',...
        'MarkerEdgeColor',colors(k,:),...
        'DisplayName',sprintf('%s First Word',name));
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

function cleanFun(err_name,good_name,temp_name,log_name)
%check if error .m file exists
if(~exist(err_name,'file'))

    prompt='Please enter notes on test conditions';
    
    %check to see if data file is missing
    if(~exist(good_name,'file'))
        %add not to say that this was an error
        prompt=[prompt,newline,'Data file missing, something went wrong'];
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

    %check to see if data file exists
    if(exist(good_name,'file'))
        %append post notes to .mat file
        save(good_name,'post_notes','-append');
    end
    
    %check to see if temp data file exists
    if(exist(temp_name,'file'))
        %append post notes to .mat file
        save(temp_name,'post_notes','-append');
    end
end
%% =====================[Stopping Condition function]=====================
function stopFlag = checkStopCondition(success, clip_ix, ts_ix)
% success: array of MRT success values for all trials computed so far
% clip_ix: indices of trials for specific audio clip
% ts_ix: indices of trials from latest timestep

% p-value threshold: Threshold for accepting observed value or not. The
% higher alpha is the "stricter" our stopping criteria is. 
alpha = 0.05;

% Isolate scores for p1 and p2 (first and second play of the word)
% % p1 only care about success results from trials at last timestep
p1_success = success(1,ts_ix);
% % p2 care about all trials so far for given clip
p2_success = success(2,clip_ix);

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
