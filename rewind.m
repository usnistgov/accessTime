function rewind(filename,num,newname)
%REWIND - rewind a temporary data file by a given number of trials
%       Warning this function has been lightly tested and may have errors
%       that cause it to function incorrectly. Use at your own risk
%
%   REWIND('tempfile.mat',150,'newfile.mat') - rewind tempfile.mat by 150
%   trials and save it in nwfile.mat

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

save_vars={'git_status','y','dev_name','test_dat','ptt_st_dly','cutpoints',...
           'fs','test_info','p','AudioFiles','stopFlag','file_status',...
        ...%save pre test notes, post test notes will be appended later
           'pre_notes'};
     
%for partial data files there are extra vars that must be saved. These are
%not in the final datafile.
partial_vars={'trialCount','clip','k','kk'};

%% ===================[load in old data file if given]===================

%load in new datafile, overwrites input arguments
load(filename,save_vars{:},partial_vars{:});
%check file_status from saved file
if(~strcmp(file_status,'partial'))
    error('File ''%s'' is not a partial save file. can be rewound.',dfile);
end

%% ===========================[Check trialCount]===========================

if(trialCount<=num)                                                         %#ok Read from file
    error('File has %d trials so rewinding %i trials is impossible',trialCount,num);
end

%% =============================[Rewind Loop]=============================

%create a backwards loop to rewind
for n=1:num
    trialCount=trialCount-1;
    kk=kk-1;
    if(kk==0)
        k=k-1;
        kk=p.Results.PTTrep;
        if(k==0)
            clip=clip-1;
            k=length(ptt_st_dly{clip});                                     %#ok Read from file
            kk=p.Results.PTTrep;
        end
    end
end

%% ============================[Save new file]============================

%save out new file
save(newname,save_vars{:},partial_vars{:});
