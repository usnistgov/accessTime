classdef ABC_MRT16
% ABC_MRT16 - create an ABC_MRT16 object
%
% obj = ABC_MRT16() create a new ABC_MRT16 object. This loads in the speech
% templates for the MRT words. The object can then be used to calculate
% intelligibility for audio clips.
%
% ABC_MRT Method:
%   process - calculate of speech intelligibility with ABC-MRT16
    
    
%--------------------------Background--------------------------
%ABC_MRT16.m implements the ABC-MRT16 algorithm for objective estimation of 
%speech intelligibility.  The algorithm is discussed in detail in [1] and
%[2].
%
%The Modified Rhyme Test (MRT) is a protocol for evaluating speech
%intelligibility using human subjects [3]. The subjects are presented
%with the task of identifying one of six different words that take the
%phonetic form CVC.  The six options differ only in the leading or
%trailing consonant. MRT results take the form of success rates
%(corrected for guessing) that range from 0 (guessing) to 1 
%(correct identification in every case).  These success rates form a 
%measure of speech intelligibility in this specific (MRT) context.
%
%The 2016 version of Articulation Band Correlation-MRT, (ABC-MRT16) is a 
%signal processing algorithm that processes MRT audio files and produces
%success rates.
%
%The goal of ABC-MRT16 is to produce success rates that agree with those
%produced by MRT. Thus ABC-MRT16 is an automated or objective version of
%MRT and no human subjects are required. ABC-MRT16 uses a very simple and
%specialized speech recognition algorithm to decide which word was spoken.
%This version has been tested on narrowband, wideband, superwideband,
%and fullband speech.
%
%Information on preparing test files and running ABC_MRT16.m can be found
%in the readme file included in the distribution.  ABC_MRTdemo16.m shows
%example use.
%
%--------------------------References--------------------------
%[1] S. Voran "Using articulation index band correlations to objectively
%estimate speech intelligibility consistent with the modified rhyme test,"
%Proc. 2013 IEEE Workshop on Applications of Signal Processing to Audio and
%Acoustics, New Paltz, NY, October 20-23, 2013.  Available at
%www.its.bldrdoc.gov/audio.
%
%[2] S. Voran " A multiple bandwidth objective speech intelligibility 
%estimator based on articulation index band correlations and attention,"
%Proc. 2017 IEEE International Conference on Acoustics, Speech, and 
%Signal Processing, New Orleans, March 5-9, 2017.  Available at
%www.its.bldrdoc.gov/audio.
%
%[3] ANSI S3.2, "American national standard method for measuring the 
% intelligibility of speech over communication systems," 1989.
%
%--------------------------Legal--------------------------
%THE NATIONAL TELECOMMUNICATIONS AND INFORMATION ADMINISTRATION,
%INSTITUTE FOR TELECOMMUNICATION SCIENCES ("NTIA/ITS") DOES NOT MAKE
%ANY WARRANTY OF ANY KIND, EXPRESS, IMPLIED OR STATUTORY, INCLUDING,
%WITHOUT LIMITATION, THE IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR
%A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY.  THIS SOFTWARE
%IS PROVIDED "AS IS."  NTIA/ITS does not warrant or make any
%representations regarding the use of the software or the results thereof,
%including but not limited to the correctness, accuracy, reliability or
%usefulness of the software or the results.
%
%You can use, copy, modify, and redistribute the NTIA/ITS developed
%software upon your acceptance of these terms and conditions and upon
%your express agreement to provide appropriate acknowledgments of
%NTIA's ownership of and development of the software by keeping this
%exact text present in any copied or derivative works.
%
%The user of this Software ("Collaborator") agrees to hold the U.S.
%Government harmless and indemnifies the U.S. Government for all
%liabilities, demands, damages, expenses, and losses arising out of
%the use by the Collaborator, or any party acting on its behalf, of
%NTIA/ITS' Software, or out of any use, sale, or other disposition by
%the Collaborator, or others acting on its behalf, of products made
%by the use of NTIA/ITS' Software.

    properties (Access = private,Constant=true)
        alignbins=[7 8 9]; %FFT bins to use for time alignment
        AI=sparse(makeAI); %Make 21 by 215 matrix that maps 215 FFT bins to 21 AI bands
    end
    properties (Access = private)
        templates   %templates for data
        binsPerBand %number of FFT bins in each AI band
    end
    
    methods
        function obj=ABC_MRT16()
% ABC_MRT16 - create an ABC_MRT16 object
%
% obj = ABC_MRT16() create a new ABC_MRT16 object. This loads in the speech
% templates for the MRT words. The object can then be used to calculate
% intelligibility for audio clips.
           
            %The file ABC_MRT_FB_templates.mat contains a 1 by 1200 cell
            %array called TFtemplatesFB.  Each cell contains a fullband
            %time-frequency template for one of the 1200 talker x keyword
            %combinations.
            obj.templates=load('ABC_MRT_FB_templates.mat');
            obj.binsPerBand=sum(obj.AI,2); %number of FFT bins in each AI band
        end
            
        
        function [phi_hat,success]= process(obj,speech,file_num,varargin)
%process - calculate of speech intelligibility with ABC-MRT16
%
%   [phi_hat,success]= PROCESS(speech,file_num) calculates the
%   intelligibility of the speech given in the cell array speech. file_num
%   gives the word number  and should have the same number of elements as
%   speech. The average intelligibility, corrected for guessing, over all
%   words is given by phi_hat. The intelligibility of each individual word,
%   not corrected for guessing, is returned in success.
            
            
            %create new input parser
            p=inputParser();

            %add speech input parameter
            addRequired(p,'speech',@validateSpeech);

            %add condition number parameter
            function fileNumCheck(x)
                validateattributes(x,{'numeric'},{'vector'});
                numCheck = all(arrayfun(@(n) isnan(n) || isnumeric(n) && n>0 && n <=1200 && floor(n) == n,x));
                if(~numCheck)
                    error('Element was not either NaN or positive, non-zero, <=1200, integer')
                end
            end
            addRequired(p,'file_num',@fileNumCheck);

            %add verbose parameter
            addParameter(p,'Verbose',false,@(t)validateattributes(t,{'numeric','logical'},{'scalar'}));
            
            %parse inputs
            parse(p,speech,file_num,varargin{:});

            %check if we have only one speech file
            if(~iscell(speech))
                speech={speech};
            end

            %pad speech to minimum size
            speech=cellfun(@padSpeech,speech,'UniformOutput',false);
            success=zeros(size(speech));

                for k=1:length(speech)
                    
                    %calculate autocorrelation for speech
                    xcm=min(xcorr(speech{k},'coeff'));
                    
                    %check for empty speech vector
                    if (isempty(speech{k}) || isnan(file_num(k)))
                        success(k)=NaN;
                        %check for speech using autocorrelation
                        %If the signals are periodic than there will be
                        %anticorrelation if the signals are noise then there will
                        %not be anticorrelation.
                        %NaN is returned from xcorr if the autocorrelation at lag
                        %zero is 0 because of normalization
                    elseif(xcm>-0.1 || isnan(xcm))
                        %speech not detected, skip algorithm
                        success(k)=0;
                        if p.Results.Verbose
                            warning('In clip #%d, speech not detected',k);
                        end
                    else
                        if p.Results.Verbose
                            fprintf('Working on clip %d of %d\n',k,length(speech));
                        end
                        C=zeros(215,6);
                        
                        %Create time-freq representation and apply Stevens' Law
                        X=abs(T_to_TF(speech{k})).^.6;
                        
                        %Pointer that indicates which of the 6 words in the list was spoken
                        %in the .wav file. This is known in advance from file_num.
                        %As file_num runs from 1 to 1200, correct word runs
                        %from 1 to 6, 200 times.
                        correctword=rem(file_num(k)-1,6)+1;
                        
                        %Pointer to first of the six words in the list associated with the
                        %present speech file. As file_num runs from 1 to 1200, first_word
                        %is 1 1 1 1 1 1 7 7 7 7 7 7 ...1195 1195 1195 1195 1195 1195.
                        first_word=6*(floor((file_num(k)-1)/6)+1)-5;
                        
                        %Compare the computed TF representation for the input .wav file
                        %with the TF templates for the 6 candidate words
                        for word=1:6
                            %Find number of columns (time samples) in template
                            ncols=size(obj.templates.TFtemplatesFB{first_word-1+word},2);
                            %Do correlation using a group of rows to find best time
                            %alignment between X and template
                            shift=group_corr(X(obj.alignbins,:),obj.templates.TFtemplatesFB{first_word-1+word}(obj.alignbins,:));
                            %Extract and normalized the best-aligned portion of X
                            XX=TFnorm(X(:,shift+1:shift+ncols));
                            %Find correlation between XX and template, one result per FFT
                            %bin
                            C(:,word)=sum(XX.*obj.templates.TFtemplatesFB{first_word-1+word},2);
                        end
                        C=(obj.AI*C)./repmat(obj.binsPerBand,1,6); %Aggregate correlation values across each AI band
                        C=max(C,0); %Clamp
                        
                        [SAC, ~]=sort(C,'descend');
                        %For each of the 6 word options, sort the 21 AI band correlations
                        %from largest to smallest
                        SAC=SAC(1:16,:);
                        %Consider only the 16 largest correlations for each word
                        [~,loc]=max(SAC,[],2);
                        %Find which word has largest correlation in each of these 16 cases
                        success(k)=mean(loc==correctword);
                        %Find success rate (will be k/16 for some k=0,1,...,16)
                    end
                end
            %Average over files and correct for guessing
            cprime=(6/5)*(mean(success)-(1/6));
            %No affine transformation needed
            phi_hat=cprime;
        end
    end
end

function AI=makeAI
    %This function makes the 21 by 215 matrix that maps FFT bins 1 to 215 to 21
    %AI bands. These are the AI bands specified on page 38 of the book: 
    %S. Quackenbush, T. Barnwell and M. Clements, "Objective measures of
    %speech quality," Prentice Hall, Englewood Cliffs, NJ, 1988.
    AIlims=[4     4 %AI band 1
            5     6
            7     7
            8     9
            10    11
            12    13
            14    15
            16    17
            18    19
            20    21
            22    23
            24    26
            27    28
            29    31
            32    35
            36    40 %AI band  16    
            41    45 %AI band 17
            46    52 %AI band  18
            53    62 %AI band  19
            63    76 %AI band  20
            77   215]; %Everything above AI band 20 and below 20 kHz makes 
        %"AI band 21"

    AI=zeros(21,215);
    for k=1:21
        firstfreq=AIlims(k,1);
        lastfreq=AIlims(k,2);
        AI(k,firstfreq:lastfreq)=1;
    end
end

function validateSpeech(s)
    %check if speech is a cell
    if(iscell(s))
        %check that s is a cell vector
        if(~isvector(s))
            error('Speech must be a numeric vector or cell array of numeric vectors');
        end
        
        %check if all elements are speech vectors
        cellfun(@validateSpeechVector,s);
        
    elseif(isvector(s) && isnumeric(s))
        validateSpeechVector(s);
    else
        error('Speech must be a numeric vector or cell array of numeric vectors');
    end
end
    
function validateSpeechVector(sv)

    %check if speech is a vector
    if(~isvector(sv))
        error('Speech vector must be a vector');
    end
    
    %check if speech vector is numeric
    if(~isnumeric(sv))
        error('Speech vector must be numeric');
    end
end
 
function s=padSpeech(s)
    %minimum speech vector length
    minLen=42000;
    
    %get length of speech vector
    l=length(s);
    
    if(l<minLen)
        %fill in zeros at the end
        s((l+1):minLen)=0;
    end
end
 
function X=T_to_TF(x)
    %This function generates a time-frequency representation for x using
    %the length 512 periodic Hann window, 75% window overlap, and FFT
    % - returns only the first 215 values
    % - x must be column vector
    % - zero padding is used if necessary to create samples for final full window.
    % - window length must be evenly divisible by 4
    m=length(x);
    n=512;
    nframes=ceil((m-n)/(n/4))+1;
    newm=(nframes-1)*(n/4)+n;
    x=[x;zeros(newm-m,1)];
    X=zeros(n,nframes);
    win=.5*(1-cos(2*pi*(0:511)'/512)); %periodic Hann window;
    for i=1:nframes
        start=(i-1)*(n/4)+1;
        X(:,i)=x(start:start+n-1).*win;
    end
    X=fft(X);
    X=X(1:215,:);
end

function Y=TFnorm(X)
    %This function removes the mean of every row of TF representation
    %and scales each row so sum of squares is 1.
    n=size(X,2);
    X=X-(sum(X,2)/n)*ones(1,n);
    Y=X./repmat(sqrt(sum(X.^2,2)),1,n);
end

function shift=group_corr(X,R)
    %This function uses all rows of X and R together in a cross-correlation
    % - number of rows in X and R must match
    % - X must have no fewer columns than R
    % - evaluates all possible alignments of R with X
    % - returns the shift that maximizes correlation value
    % - if R has q columns then a shift value s means that R is best
    %   aligned with X(:,s+1:s+q)
    % - assumes R is already normalized for zero mean in each row and 
    %   each row has sum of squares = 1

    [~,n]=size(X);
    [~,q]=size(R);

    nshifts=n-q+1;
    C=zeros(nshifts,1);
    for i=1:nshifts
        T=X(:,i:i+q-1);
        T=T-(sum(T,2)/q)*ones(1,q);
        kk=sqrt(sum(T.^2,2));
        T=T./repmat(kk,1,q);
        C(i)=sum(sum(T.*R));
    end
    [~,shift]=max(C);
    shift=shift-1;
end
