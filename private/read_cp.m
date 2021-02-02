function [cutpoints]=read_cp(fname)
    file=fopen(fname,'r');
    dat=textscan(file,'%f%u%u%[^\n\r]','Delimiter',',','EndOfLine','\r\n','HeaderLines',1, 'ReturnOnError', false);
    fclose(file);
    cutpoints=cell2mat(cellfun(@double,dat(:,1:3),'UniformOutput',false));