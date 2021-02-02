function [dat,aname,fs]=load_dat(fname)
%LOAD_DAT fucnition to load test data from csv file
%
%   dat=LOAD_DAT(fname) loads data from file with name fname. discards
%   header data
%
%   [dat,aname,fs]=LOAD_DAT(fname) same as above but returns the audio file
%   name and sample rate from header
%
    
    %cell array of columns that are allowed to be NaN
    nan_ok_cols={'TimeGap'};
    % Open file to read header data
    infile = fopen(fname,'r');
    %check for error
    if(infile==-1)
        %return empty dat
        dat={};
        aname='';
        fs='';
        return;
    end
    %read one line for audio file
    aname_raw=fgetl(infile);
    %split filename on equals sign
    aname_split = strsplit(aname_raw,'=');
    %last part is filename 
    aname=aname_split{end};
    %read one line for fs
    fs_raw=fgetl(infile);
    %split into parts
    fs_split = strsplit(fs_raw, '=');
    %convert last part to double
    fs = str2double(fs_split{end});
    fclose(infile);
    
    dat=readtable(fname);
    %get number of columns found
    cols=width(dat);
    %check for correct number of columns
    % allow for empty file
    if(cols~=0 && cols<9)
        error('Bad file format for ''%s'' not able to restore',fname);
    end
    %get the last row
    last_row=dat(end,:);
    %set fields that are allowed to be NaN to zero
    for k=1:length(nan_ok_cols)
        last_row.(nan_ok_cols{k})=0;
    end
    %check if all columns in the last row have data
    bad=cellfun(@(d)isempty(d) || any(isnan(d)),table2cell(last_row));
    %check that the last row is fully populated
    if(any(bad(1:min(end,10))))
        error('Error in data file ''%s'', partial row found',fname)
    end