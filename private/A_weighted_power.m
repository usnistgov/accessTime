function s=A_weighted_power(x,fs)
%Usage:  s=A_weighted_power(x,fs)
%Calculates an A-weighted power level in dB for the input audio vector x.
%This is a good approximation to relative loudness because the A-weighting
%function emulates a fundamental attribute of human hearing.
%fs is an optional sample rate:
%8000, 16000, 24000, 32000, or 48000 smp/sec are allowed. 
%fs defaults to 48,000 smp/sec if not specified.
%
%The filter coefficients come from dsprelated.com and the resulting
%frequency response agrees with those shown in the literature.
%Getting filter coefficients for sample rates other than 48,000 proved
%difficult so this code just converts input signals to 48,000 instead.
%S. Voran, Sept. 25, 2012

%Coeffs for A-weighting filter with fs=48k
b(1) = 0.01147155239724;
b(2) = -0.0248548824653166;
b(3) = 0.0323052801494283;
b(4) = -0.0555571372813964;
b(5) = 0.233784933167266;
b(6) = 0.392882400411297;
b(7) = -0.633249911806281;
b(8) = -0.479494344932334;
b(9) = 0.322061493940389;
b(10) = 0.197659563091056;
b(11) = 0.00299879461389451;

a(1) = 1;
a(2) =  -0.925699454182466;
a(3) =  -0.992471193943543;
a(4) =  0.837650096562845;
a(5) =  0.22307303912603;
a(6) =  -0.158404327757755;
a(7) =  0.0184103295763937;

b=b*1.1389; %set gain at 1 kHz to 0 dB

if nargin==1,fs=48000;end

if fs==8000
    x=resample(x,6,1);
elseif fs==16000
    x=resample(x,3,1);
elseif fs==24000
    x=resample(x,2,1);
elseif fs==32000
    x=resample(x,3,2);
elseif fs~=48000
    error('Unsupported sample rate.')
end

x=filter(b,a,x);
s=10*log10(mean(x.^2));
