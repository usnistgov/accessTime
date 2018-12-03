function [idx] = log_MfSearch(log,search)

    %make sure that search_field is a field
    if(~isstruct(search))
        error('search must be a struct');
    end

    %find which log entries match the search_term for search_field
    match_term=arrayfun(@(l)logMatch(l,search),log);
    
    %get the index of matches
    idx=find(match_term);
end

function res=logMatch(l,s)
    %get fieldnames
    sfeilds=fieldnames(s);
    
    %get boolean fields, these are treated differently
    boolFields=log_bool();
    
    %default to match if no fields given
    res=true;
    
    %loop over field names and check for match
    for k=1:length(sfeilds)
        %check if date_before is given
        if(strcmp(sfeilds{k},'date_before'))
            %check if field is nonempty, if not skip it
            if(~isempty(s.date_before) && ~isnat(s.date_before))
                if(s.date_before>l.date)
                    %date is earlier than date_before
                    res=true;
                else
                    %date is out of date range
                    res=false;
                    %not a match, return
                    return;
                end
            end
        elseif(strcmp(sfeilds{k},'date_after'))
            %check if field is nonempty, if not skip it
            if(~isempty(s.date_after) && ~isnat(s.date_after))
                if(s.date_after<l.date)
                    %date is later than date_after
                    res=true;
                else
                    %date is out of date range
                    res=false;
                    %not a match, return
                    return;
                end
            end
        elseif(any(strcmp(sfeilds{k},boolFields)))
            %check if field is nonempty, if not skip it
            if(~isempty(s.(sfeilds{k})))
                %check that field matches
                if(s.(sfeilds{k})==l.(sfeilds{k}))
                    %fields match
                    res=true;
                else
                    %fields do not match
                    res=false;
                    %not a match, return
                    return;
                end
            end
        else
            %check if field is nonempty, if not skip it
            if(~isempty(s.(sfeilds{k})))
                %check if fields match
                if(ischar(l.(sfeilds{k})) && ~isempty(regexp(l.(sfeilds{k}),s.(sfeilds{k}),'once')))
                    %fields match
                    res=true;
                else
                    %fields do not match
                    res=false;
                    %not a match, return
                    return;
                end
            end
        end
    end
end
                    