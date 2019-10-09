function [nb]=align_audio(a,b,fs,varargin)
%remove delay from audio
%   [nb] = ALIGN_AUDIO(a,b,fs) return a version of b that is aligned with a
%
%   [nb] = ALIGN_AUDIO(a,b,fs,'Skip',time) same as above but skips the
%   first time seconds of the audio when computing mout-to-ear latency


%create new input parser
p=inputParser();

%add reference signal argument
addRequired(p,'a',@(n)validateattributes(n,{'numeric'},{'vector','nonempty'}));
%add test signal argument
addRequired(p,'b',@(n)validateattributes(n,{'numeric'},{'vector','nonempty'}));
%add sample rate argument
addRequired(p,'fs',@(n)validateattributes(n,{'numeric'},{'scalar','positive','nonempty'}));
%add skip parameter
addParameter(p,'Skip',0,@(t)validateattributes(t,{'numeric'},{'scalar','nonnegative'}));

%parse inputs
parse(p,a,b,fs,varargin{:});

%sample rate for ITS delay
fs_ITS_dly=8e3;

%calculate resample factors
[p_ITS_dly,q_ITS_dly]=rat(fs_ITS_dly/fs);

%calculate starting index for alignment
skip_idx=max(round(p.Results.Skip*fs),1);

% %calculate average delay
% dly=mean(1e-3*ITS_delay_wrapper(b(skip_idx:end),a(skip_idx:end),fs));

tmp = 1/fs_ITS_dly*ITS_delay_wrapper(...,
    resample(a(skip_idx:end),p_ITS_dly,q_ITS_dly),...
    resample(b(skip_idx:end),p_ITS_dly,q_ITS_dly),...
    'f');

%calculate delay
dly=tmp(2);

%generate time vector for a
t_a=((1:length(a))-1)/fs;

%generate time vector for b
t_b=((1:length(b))-1)/fs-dly;

%generate interpolant
b_interp=griddedInterpolant(t_b,b,'linear','none');

%interpolate envelope to get rid of time shift
nb=b_interp(t_a);
