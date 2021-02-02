function pause_needed=example_restart(calls,trialCount,clip_count)

    if(calls>2)
        %function has been called to many times for this clip
        
        pause_needed=1;
        return
    end
    
    %call python script which does the real work
    %will need to have a compatible python installed
    py.example_adb.restart_all()
    
    pause_needed=1;
    
end