function [idx] = log_MfSearch(log,search)
% log_MfSearch search a log structure for a test matching given criteria
%   [idx] = log_MfSearch(log,search) searches log for entries that match
%   the search criteria given in search. The indices of the matching
%   entries are returned in idx
%
%   log is a structure array of log entries returned by log_search
%
%   search is a structure that contains the search criteria. With the
%   exception of the date field, to search for a field in the log structure
%   a corosponding field in the search structure will search for a matching
%   field in the log structure. 
%
%   Fieldname(s)    Datatype        Matching type
%
%   date            DateTime        in the search structure there are two
%                                   fields date_befor and date_after. These
%                                   specify a range of log timestamps to
%                                   search for that is after date_after and
%                                   before date before.
%
%   error,complete  logical         all returned log entries match the
%                                   value in the search structure exactly
%
%   others          char array      log entries are scanned for matching
%                                   strings using regexp with the pattern
%                                   in the search structure
%


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
    sfields=fieldnames(s);
    
    %get boolean fields, these are treated differently
    boolFields=log_bool();
    
    %default to match if no fields given
    res=true;
    
    %loop over field names and check for match
    for k=1:length(sfields)
        %check if date_before is given
        if(strcmp(sfields{k},'date_before'))
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
        elseif(strcmp(sfields{k},'date_after'))
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
        elseif(any(strcmp(sfields{k},boolFields)))
            %check if field is nonempty, if not skip it
            if(~isempty(s.(sfields{k})))
                %check that field matches
                if(s.(sfields{k})==l.(sfields{k}))
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
            if(~isempty(s.(sfields{k})))
                %check if fields match
                if(ischar(l.(sfields{k})) && ~isempty(regexp(l.(sfields{k}),s.(sfields{k}),'once')))
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
                    