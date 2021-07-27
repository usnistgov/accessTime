
from warnings import warn

def terminal_progress_update(
            prog_type,
            num_trials,
            current_trial,
            msg="",
            clip_name="",
            delay="",
            file="",
            new_file="",
        ):
    if (prog_type == 'proc'):
        if (current_trial == 0):
            #we are post processing
            print('Processing test data')
        if (current_trial % 10 == 0):
            print(f'Processing trial {current_trial} of {num_trials}')   
    elif (prog_type == 'test'):
        if (current_trial == 0):
            print(f'Starting Test of {num_trials} trials')
        if (current_trial % 10 == 0):
            print(f'-----Trial {current_trial} of {num_trials}')
    elif (prog_type == 'warning'):
        warn(msg, stacklevel=2)
    elif (prog_type == 'check-fail'):
        print(f'On trial {current_trial} of {num_trials} : {msg}')
    elif (prog_type == 'check-resume'):
        print(f'Resuming test : {msg}')
    elif (prog_type == 'acc-clip-update'):
        print(f'---Delay : {delay:.3f}s\n'+
              f'---Clip  : {clip_name}')
    elif (prog_type == 'csv-update'):
        # Print name and location of datafile    
        print(f'--Starting {clip_name}\n'+
              f'--Storing data in: \'{file}\'')
    elif (prog_type == 'csv-rename'):
        print(f"Renaming '{file}' to '{new_file}'")
    elif prog_type == "status":
        print(msg)
        
    #continue test
    return True
    
def terminal_user_check(reason,message, trials=None, time=None):
    abort_test = False
    #check if we have time and trials
    if (trials and time):
        # Print set time
        print(f"Time for {trials} trials : {time}")
    #ask the user to press enter to continue
    #ring bell ('\a') to get their attention
    resp = input('\a'+
               message+' Press enter to continue\n'+
               'you may type "exit" to stop the test\n')
    if (resp.lower().strip() == 'exit'):
        abort_test = True
    
    return abort_test
    