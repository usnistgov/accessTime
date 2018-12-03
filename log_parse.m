function log=log_parse(fname)

f=fopen(fname,'r');

l='';
%parser status
status='searching';

%create empty structure for data
log=struct([]);
%index in structure array
idx=0;
%line count
lc=0;

while(all(~isnumeric(l)))
    l=fgetl(f);
    
    %check for end of file
    if(isnumeric(l))
        break;
    end
    
    %advance linecount
    lc=lc+1;

    %always check for start of entry
    if(startsWith(l,'>>'))
        %check if we were in search mode
        if(~strcmp(status,'searching'))
            %give warning when start found out of sequence
            warning('Start of packet found at line %d while in %s mode',lc,status);
        end
        %start of entry found, now we will parse the preamble
        status='preamble-st';
    end
    
    switch(status)
        case 'searching'
            
        case 'preamble-st'
            %advance index
            idx=idx+1;
            
            %split string into date and operation
            parts=strsplit(strtrim(l),' at ');
            
            %set date
            log(idx).date=datetime(parts{2},'InputFormat','dd-MMM-yyyy HH:mm:ss');
            
            %operation is the first bit
            op=parts{1};
            
            %remove >>'s from the begining
            op=op(3:end);
            
            %remove trailing ' started'
            if(endsWith(op,' started'))
                op=op(1:(end-length(' started')));
            end
            
            %set operation
            log(idx).operation=op;
            
            %flag entry as incomplete
            log(idx).complete=false;
            
            %initialize error flag
            log(idx).error=false;
            
            %set status to preamble
            status='preamble';
        case 'preamble'
            
            %check that the first charecter is not tab
            if(~isempty(l) && l(1)~=9)
                %check for three equal signs
                if(~startsWith(l,'==='))
                    warning('Unknown sequence found in preamble at line %d : %s',lc,l);
                    %drop back to search mode
                    status='searching';
                elseif(startsWith(l,'===End'))
                    %end of entry, go into search mode
                    status='searching';
                    %mark entry as complete
                    log(idx).complete=true;
                else
                    switch(l)
                        case '===Pre-Test Notes==='
                            status='pre-notes';
                            %create empty pre test notes field
                            log(idx).pre_notes='';
                        case '===Post-Test Notes==='
                            status='post-notes';
                            %create empty post test notes field
                            log(idx).post_notes='';
                        otherwise
                            warning('Unknown seperator found in preamble at line %d : %s',lc,l);
                            %drop back to search mode
                            status='searching';
                    end
                end
            else
                %split line on colen
                lp=strsplit(l,':');
                name=genvarname(lp{1});
                arg=lp{2};
                for k=3:length(lp)
                    %recnostruct line
                    arg=strcat(arg,':',lp{k});
                end
                
                %check if field exists in structure
                if(isfield(log(idx),name) && ~isempty(log(idx).(name)))
                    warning('Duplicate field %s found at line %d',name,lc);
                else
                    log(idx).(name)=arg;
                end
            end
        case 'pre-notes'
            %check that the first charecter is a tab
            if(~isempty(l) &&  l(1)==9)
                %add in line, skip leading tab
                log(idx).pre_notes=strcat(log(idx).pre_notes,l(2:end));
            else
                %check for three equal signs
                if(~startsWith(l,'==='))
                    warning('Unknown sequence found in %s at line %d : %s',status,lc,l);
                    %drop back to search mode
                    status='searching';
                elseif(startsWith(l,'===End'))
                    %end of entry, go into search mode
                    status='searching';
                    %mark entry as complete
                    log(idx).complete=true;
                else
                    switch(l)
                        case '===Post-Test Notes==='
                            status='post-notes';
                            %create empty post test notes field
                            log(idx).post_notes='';
                        case '===Test-Error Notes==='
                            status='post-notes';
                            %create empty test error notes field
                            log(idx).error_notes='';
                            log(idx).error=true;
                        otherwise
                            warning('Unknown seperator found in %s at line %d : %s',status,lc,l);
                            %drop back to search mode
                            status='searching';
                    end
                end
            end
        case 'post-notes'
            %check that the first charecter is a tab
            if(~isempty(l) && l(1)==9)
                if(log(idx).error)
                    %add in line, skip leading tab
                    log(idx).error_notes=strcat(log(idx).error_notes,l(2:end));
                else
                    %add in line, skip leading tab
                    log(idx).post_notes=strcat(log(idx).post_notes,l(2:end));
                end
            else
                %check for three equal signs
                if(~startsWith(l,'==='))
                    warning('Unknown sequence found in %s at line %d : %s',status,lc,l);
                    %drop back to search mode
                    status='searching';
                elseif(startsWith(l,'===End'))
                    %end of entry, go into search mode
                    status='searching';
                    %mark entry as complete
                    log(idx).complete=true;
                else
                    warning('Unknown seperator found in %s at line %d : %s',status,lc,l);
                    %drop back to search mode
                    status='searching';
                end
            end
    end
end

fclose(f);
