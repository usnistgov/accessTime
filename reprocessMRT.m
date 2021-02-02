function [phi_hat, success, rec_a, new_m2e, test_dat, dec_sp] = reprocessMRT(fname,varargin)
% REPROCESSMRT reprocess MRT scores for a test
%
%   reprocessMRT(fname) reprocess the MRT scores in the mat file fname
%   with no time expansion. Default time expansion setting in an access
%   delay test is T/2.
%
%   reprocessMRT(fname,name,value) same as above but specify parameters as
%   name value pairs. Possible name value pairs are shown below
%
%   NAME                TYPE                Description
%
%   fs                  double              Sampling rate of audio
%
%   pad                 logical             Force all recordings to be the
%                                           same length. Recordings filled
%                                           with NaN values.
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

%create new input parser
p=inputParser();

%add filename parameter
addRequired(p,'fname',@(n)validateattributes(n,{'char'},{'vector','nonempty'}));

addParameter(p,'fs',[],@(t)validateattributes(t,{'numeric'},{'scalar'}));

% add parameter to reprocess MRT with bigger windows
addParameter(p,'TimeExpand',[],@validate_expand);
% add parameter for where data is stored
addParameter(p,'datdir','',@(t)validateattributes(t,{'char'},{'vector','nonempty'}));

% addParameter to reprocess m2e latency
addParameter(p,'recalc_m2e',false,@(t)validateattributes(t,{'numeric','logical'},{'scalar'}));
% addParameter to enable saving individual word files
addParameter(p,'WordWavs',false,@(t)validateattributes(t,{'numeric','logical'},{'scalar'}));
% addParameter to enable saving a singele wave
addParameter(p,'OneWav',false,@(t)validateattributes(t,{'numeric','logical'},{'scalar'}));


%parse inputs
parse(p,fname,varargin{:});

recalc_m2e = p.Results.recalc_m2e;

[ffold,fbase,fext]=fileparts(fname);

f_be=[fbase fext];

if(isempty(p.Results.datdir))
    %get csv directory from filename
    csv_parentdir=ffold;
    
    %fileparts on a directory name gets parent directory
    [pp_dir,~]=fileparts(ffold);
    
    wav_parentdir = fullfile(pp_dir,'wav');
else
    % Get wav directory from datdir
    wav_parentdir = fullfile(p.Results.datdir,'post-processed data','wav');

    % Get csv directory from datdir
    csv_parentdir = fullfile(p.Results.datdir,'post-processed data','csv');
end

%print things so we know what is going on
fprintf('Loading data file\n');

%check if full path for file was given
if(isempty(ffold))
    % Get csv name
    csv_name = fullfile(csv_parentdir, f_be);
else
    csv_name=fname;
end
    
% Read all test data
[test_dat,audioname,fs] = load_dat(csv_name);

% get audio clip name without path
[~,clipname] = fileparts(audioname);

% Get total number of tests
trials = height(test_dat);

fparts = strrep(f_be,['_' clipname '.csv'],'');
wav_dir = fullfile(wav_parentdir,fparts);

% Read transmit audio
tx_name = ['Tx_' clipname '.wav'];
tx_path = fullfile(wav_dir, tx_name);
y = audioread(tx_path);

% Read cutpoints file
cp_name = strrep(tx_name,'.wav','.csv');
cp_path = fullfile(wav_dir,cp_name);
cutpoints = read_cp(cp_path);

%sample rate for ITS delay
fs_ITS_dly=8e3;

%calculate resample factors
[p_ITS_dly,q_ITS_dly]=rat(fs_ITS_dly/fs);

%% =========================[Setup wav output dir]=========================
if(p.Results.WordWavs)
    wave_out_dir=fullfile('.',fbase);

    [~,~,~]=mkdir(wave_out_dir);
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
        %set time expand from parm, force row vector
        TimeExpand=reshape(p.Results.TimeExpand,1,[]);
    else
        error('internal error setting TimeExpand');
    end
end



%%
%preallocate
phi_hat=zeros(trials,1);
success=zeros(2,trials);
dec_sp=cell(trials,2);

rec_a = cell(length(y),1);

fprintf('Creating MRT object\n');
%initialize MRT object
MRT_obj=ABC_MRT16();

%generate time vector for y
t_y = (1:length(y))/fs;

new_m2e = nan(trials,1);
%%
for k=1:trials
    
    if(mod(k,round(trials/100)) == 0)
        %print things so we know what is going on
        fprintf('Trial %d of %d\n',k,trials);
    end
    
    rx_name = ['Rx' num2str(k) '_' clipname '.wav'];
    rx_path = fullfile(wav_dir,rx_name);
    % Load in appropriate recording
    recording = audioread(rx_path);
    
    if(recalc_m2e)
        % Don't start looking at delay until 1 second after PTT was set
        dly_st_idx = round((test_dat{k,'PTT_start'}+1)*fs);
        tmp=1/fs_ITS_dly*ITS_delay_wrapper(...
            resample(y(dly_st_idx:end,1)',p_ITS_dly,q_ITS_dly),...
            resample(recording(dly_st_idx:end,1),p_ITS_dly,q_ITS_dly),...
            'f',...
            'dlyBounds',[0,Inf]);
        m2e = tmp(2);
        new_m2e(k) = tmp(2);
    else
        m2e = test_dat{k,'m2e_latency'};
    end
    
    %interpolate for new time.
    rec_int=griddedInterpolant((1:length(recording(:,1)))/fs-m2e,recording(:,1));
    
    %expand cutpoints by TimeExpand
    ex_cp=round(cutpoints([2,4],[2,3]) -  (TimeExpand*fs).*[1,-1]);
    
    ylen = length(y(:,1));
    ex_cp(ex_cp > ylen) = ylen;
    %minimum cutpoint index is 1
    ex_cp(ex_cp<1)=1;
    
    
    %new shifted version of signal
    rec_a{k}=rec_int(t_y);
    
    % split out words for MRT
    for kk=1:2
        dec_sp{k,kk} = rec_a{k}(ex_cp(kk,1):ex_cp(kk,2))';
    end
    
    %compute MRT scores for clips
    [phi_hat(k),success(:,k)]=...
        MRT_obj.process(dec_sp(k,:),cutpoints([2 4],1));
   
    
    if(p.Results.WordWavs)
        wav_name = fullfile(wave_out_dir,sprintf('Repr%d_%s',k,clipname));
        if(p.Results.OneWav)
            rec_p=cell(2,1);
            for kk=1:size(dec_sp,2)
                %copy of rec_a for output wav
                tmp=rec_a{k};

                %zero out other stuff
                tmp(1:ex_cp(kk,1))=0;
                tmp(ex_cp(kk,2):end)=0;
                
                %add full scale samples for marker
                tmp(ex_cp(kk,:))=1;
                tmp(ex_cp(kk,:)+[-1,1])=-1;
                
                rec_p{kk}=tmp(1:length(rec_a{k}));
            end
            wavout=vertcat(rec_a{k},rec_p{:})';
            audiowrite([wav_name '.wav'],wavout,fs);
        else
            for kk=1:size(dec_sp,2)
                audiowrite(sprintf('%s_p%d.wav',wav_name,kk),dec_sp{k,kk},fs);
            end
        end
    end
    
    
end

function validate_expand(t)
    if(~isempty(t))
        validateattributes(t,{'numeric'},{'nonnegative'})
    end
    %check if length is greater than two
    if(length(t)>2)
        error('Time Expand value must be empty or a one or two element vector.');
    end
