function state=getTestState(prompt,resp)
%GETTESTSTATE generate test state struct from cell array of prompts and responses
%
%	state=GETTESTSTATE(prompt,resp) returns a test state struct that
%	represents the state given by the prompt and responses
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


%names of fields in file
names={'Test Type','System','Tx Device','Transmit Device','Rx Device','Receive Device','3rd Device'};

%names of fields in structure
fields={'testType','System','TxDevice','TxDevice','RxDevice','RxDevice','ThirdDevice'};

%create struct to keep data
state=struct();

for k=1:length(prompt)
    %check for match
    match=strcmp(names,strtrim(prompt{k}));
    
    %check if there was a match
    if(any(match))
        %found correct name, set value
        state.(fields{match})=resp{k};
    else
        %field not found
        error('Invalid prompt ''%s''',strtrim(prompt{k}));
    end
end

%make sure all fields are present
for k=1:length(names)
    %check if field is present
    if(~isfield(state,fields{k}))
        %not present, set to empty string
        state.(fields{k})='';
    end
end

end