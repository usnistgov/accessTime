function [phi_hat, success,dat,rec_a] = reprocessMRT(fname,varargin)
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
%   timeExpand          numeric             Length of time, in seconds, of
%                                           extra audio to send to
%                                           ABC-MRT16. Adding time protects
%                                           against inaccurate M2E latency
%                                           calculations and misaligned
%                                           audio.

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

% add output padding parameter
addParameter(p,'pad',true,@(t)validateattributes(t,{'numeric','logical'},{'scalar'}));
% add parameter to reprocess MRT with bigger windows
addParameter(p,'timeExpand',0,@(t)validateattributes(t,{'numeric'},{'scalar','nonnegative'}));

%parse inputs
parse(p,fname,varargin{:});

%print things so we know what is going on
fprintf('Loading data file\n');

%variables to load from file
load_vars={'y','fs','test_dat','cutpoints'};

%get variables in file
vars=whos('-file',fname);

%check if ptt_start is in file
if(any(strcmp({vars.name},'ptt_start')))
    %add ptt_start to load_vars
    load_vars{end+1}='ptt_start';
end

%check if clip is in file
if(any(strcmp({vars.name},'clipi')))
    %add clipi to load_vars
    load_vars{end+1}='clipi';
end

%check if fs is in file
if(any(strcmp({vars.name},'fs')))
    %read fs
    load_vars{end+1}='fs';
end


%load data file
dat=load(fname,load_vars{:});

if(isfield(dat,'fs'))
    fs=dat.fs;
elseif(~isempty(p.Results.fs))
    fs=p.Results.fs;
else
    error('fs not found in ''%s'', must be passed as parameter',fname);
end

%sample rate for ITS delay
fs_ITS_dly=8e3;

%calculate resample factors
[p_ITS_dly,q_ITS_dly]=rat(fs_ITS_dly/fs);

%force y into a cell array
if(~iscell(dat.y))
    % dat.y is not a cell, make it one
    y={dat.y};
else
    % dat.y is cell, use as is
    y=dat.y;
end



%get number of trials
trials=length(dat.test_dat.recordings);

%preallocate 
phi_hat=zeros(trials,1);
success=zeros(2,trials);

rec_a = cell(length(y),1);

if(isfield(dat.test_dat,'clipi'))
    clipi = dat.test_dat.clipi;
else
    clipi =  mod((1:trials)-1,length(y))+1;
end


fprintf('Creating MRT object\n');
%initialize MRT object
MRT_obj=ABC_MRT16();

time_ex = p.Results.timeExpand;


%generate time vector for y
t_y=cellfun(@(v)(1:length(v))/fs,dat.y,'UniformOutput',false);

for k=1:trials    

    %calculate index to start M2E latency at. This is 3/4 through the
    %second silence. if more of the clip is used ITS_delay can get
    %confused and return bad values

    dly_st_idx = round(dat.cutpoints{clipi(k)}(3,2) + 0.75*diff(dat.cutpoints{clipi(k)}(3,2:3)));

    if(mod(k,round(trials/100)) == 0)
        %print things so we know what is going on
        fprintf('Trial %d of %d\n',k,trials);
    end
    
    %align audio
    %rec_a{k} = align_audio(y{clipi(k)},dat.test_dat.recordings{k}(:,1),dat.fs,'Skip',skip);

    start_ix = dat.cutpoints{clipi(k)}([2,4],2) - round(time_ex*fs);
    start_ix(start_ix<=0)=1;
    end_ix = dat.cutpoints{clipi(k)}([2,4],3) + round(time_ex*fs);

%     last_samp = length(dat.test_dat.recordings{k}(:,1));
    last_samp = length(y{clipi(k)}(:,1));
    end_ix(end_ix > last_samp) = last_samp;

    %calculate delay. Only use data after dly_st_idx
    tmp=1/fs_ITS_dly*ITS_delay_wrapper(...
        resample(y{clipi(k)}(dly_st_idx:end,1)',p_ITS_dly,q_ITS_dly),...
        resample(dat.test_dat.recordings{k}(dly_st_idx:end,1),p_ITS_dly,q_ITS_dly),...
        'f');

    %interpolate for new time. delay is in tmp(2)
    rec_int=griddedInterpolant((1:length(dat.test_dat.recordings{k}(:,1)))/fs-tmp(2),dat.test_dat.recordings{k}(:,1));

    %new shifted version of signal
    rec_a{k}=rec_int(t_y{clipi(k)});

    dec_sp = {rec_a{k}(start_ix(1):end_ix(1))';
        rec_a{k}(start_ix(2):end_ix(2))'
        };

    %compute MRT scores for clips
    [phi_hat(k),success(:,k)]=...
        MRT_obj.process(dec_sp,dat.cutpoints{clipi(k)}([2 4],1));

end

if(p.Results.pad)
    %get number of audio samples for audio array
    audioSamp=max(cellfun(@length,y));
    %pad fill with NaNs so that all are the same length
    rec_a=cellPad2Mat(rec_a,audioSamp);
end

function m=cellPad2Mat(C,len)
    %preallocate
    m=NaN(length(C),len);
    
    for k=1:length(C)
        m(k,1:length(C{k}))=C{k};
    end
    

