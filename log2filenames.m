function [names] = log2filenames(log,searchpath)
    names=arrayfun(@(l)log2filename(l,searchpath),log,'UniformOutput',false);
end

function [fn]=log2filename(log,searchpath)
    %handle diffrent opperations differently
    switch(log.opperation)
        case 'Test'
            prefix={'capture_'};
            folder={'data'};
        case 'Training'
            prefix={'Training_','Training_'};
            folder={'training','data'};
        case 'Tx Two Loc Test'
            prefix={'Tx_capture','capture'};
            folder={'tx-data','tx-data'};
        case 'Rx Two Loc Test'
            prefix={'Rx_capture','capture'};
            folder={'rx-data','rx-data'};
        otherwise
            
            %check if this was a copy opperation
            if(startsWith(log.opperation,'Copy'))
                %no datafile for Copy opperation
                fn=':None';
                return;
            end
            
            %otherwise this is an unknown opperation
            error('Unknown opperation ''%s''',log.opperation);
    end

    %check if entry is incomplete
    if(~log.complete)
        fn=':Incomplete';
        return;
    end
    
    %check if this trial had an error
    if(log.error)
        fn=':Error';
        return;
    end
    
    date=log.date;
    
    %set new format
    date.Format='dd-MMM-yyyy_HH-mm-ss';
    
    %get date string in filename format
    date_str=char(date);
    
    for k=1:length(folder)
        
        foldPath=fullfile(searchpath,folder{k});
        
        %look in the folder
        filenames=cellstr(ls(fullfile(foldPath,[prefix{k} '*'])));

        match=contains(filenames,date_str);

        num_match=sum(match);

        if(num_match>1)
            warning('More than one file found matching ''%s'' in ''%s''',date_str,foldPath);
            fn='Multiple';
        elseif(num_match==0 && k==length(folder))
            warning('No matching file for ''%s'' in ''%s''',date_str,foldPath);
            fn='';
        elseif(num_match==1)
            fn=filenames{match};
            return;
        end
    end
end

