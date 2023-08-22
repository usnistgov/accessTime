#!/usr/bin/env python
import argparse
import datetime
import mcvqoe
import numpy as np
import os
import sys

from fractions import Fraction
from mcvqoe.hardware import AudioPlayer
from mcvqoe.hardware import RadioInterface
from warnings import warn

from .access_time import measure as access_time_meas

        
def int_or_inf(input):
    """Check for 'infinite' entry, and change value  to np.inf if found"""
    try:
        return int(input)
    except ValueError as e:
        word = input.lower()
        infinite = ['inf', 'np.inf', 'math.inf', 'infinite']
        if word in infinite:
            return np.inf
        else:
            #not infinite, re throw ValueError
            raise e

import mcvqoe.gui.test_info_gui as test_info_gui
           
def main():
    
    # Create Access object
    test_obj = access_time_meas()
    # Set post test notes function
    test_obj.get_post_notes = test_info_gui.post_test
    
    #--------------------[Create AudioPlayer Object]----------------------
        
    sim_obj = AudioPlayer(
                    playback_chans = {'tx_voice':0, 'start_signal':1},
                    rec_chans = {'rx_voice':0, 'PTT_signal':1},
                    )
                    
    test_obj.audio_interface = sim_obj

    #--------------------[Parse the command line arguments]--------------------
        
    parser = argparse.ArgumentParser(description=__doc__)
    
    parser.add_argument('-a', '--audiofiles', dest="audio_files", default=test_obj.audio_files,
                        nargs="+", metavar="FILENAME", help="Audio files to use for testing."+
                        " The cutpoints for the file must exist in the same directory with"+
                        " the same name and a .csv extension. If a multiple audio files"+
                        " are given, then the test is run in succession for each file.")
    parser.add_argument('-k', '--audiopath', dest="audio_path", default=test_obj.audio_path,
                        metavar="Path", help="Path to look for audio file in. All audio"+
                        " file paths are relative to this unless they are absolute.")
    parser.add_argument('-t', '--pause-trials', type=int_or_inf,
                        default=test_obj.pause_trials, metavar="T",
                        help='Number of trials to run until a pause is ' +
                        'encountered (default: %(default)s).')
    parser.add_argument('-r', '--radioport', default='', metavar="PORT",
                        help="Port to use for radio interface. Defaults to the first"+
                        " port where a radio interface is detected.")
    parser.add_argument('-y', '--pttdelay', nargs="+", dest="ptt_delay", type=float,
                        default=test_obj.ptt_delay, help="ptt_delay can be a 1 or 2 element double"+
                        " vector. If it is a 1 element vector then it specifies the minimum"+
                        " ptt_delay that will be used with the maximum being the end of the"+
                        " first word in the clip. If a two element vector then the first"+
                        " element is the smallest delay used and the second is the largest.")
    parser.add_argument('-p', '--pttstep', dest="ptt_step", type=float, default=test_obj.ptt_step,
                        help="Time in seconds between successive pttdelays. Default is 20ms.")
    parser.add_argument('-z', '--bgnoisefile', dest="bgnoise_file", default='', help="If this is"+
                        " non empty then it is used to read in a noise file to be mixed with the "+
                        "test audio. Default is no background noise.")
    parser.add_argument('-N', '--bgnois-snr', dest="bgnoise_snr", type=float,
                        default=test_obj.bgnoise_snr,
                        help="Signal to noise ratio for background noise. "
                        "Defaults to %(default) dB."
                        )
    parser.add_argument('-s', '--pttgap', dest="ptt_gap", type=float, default=test_obj.ptt_gap,
                        help="Time to pause after completing one trial and starting the next."+
                        " (Defaults to %(default).1f s).")
    parser.add_argument('-e', '--pttrep', dest="ptt_rep", type=int, default=test_obj.ptt_rep,
                        help="Number of times to repeat a given PTT delay value. If auto_stop is "+
                        "used ptt_rep must be greater than 15. (Defaults to %(default)i)")
    parser.add_argument('-c', '--autostop', dest="auto_stop", action='store_true', default=test_obj.auto_stop,
                        help="Enable checking for access and stopping the test when it is detected.")
    parser.add_argument('--no-autostop', dest="auto_stop", action='store_false',
                        help="Disable checking for access and stopping the test when it is detected.")
    parser.add_argument('-f', '--stoprep', dest="stop_rep", type=int, default=test_obj.stop_rep,
                        help="Number of times that access must be detected in a row before the"+
                        " test is completed. (Defaults to %(default)i)")
    parser.add_argument('-g', '--devdly', dest="dev_dly", type=float, default=test_obj.dev_dly,
                        help="Delay in seconds of the audio path with no communication device"+
                        " present. (Defaults to %(default).4f s)")
    parser.add_argument('-m', '--datafile', dest="data_file", default=test_obj.data_file,
                        help="Name of a temporary datafile to use to restart a test. If this is"+
                        " given all other parameters are ignored and the settings that the original"+
                        " test was given are used. Needs full path name.")
    parser.add_argument('-x', '--timeexpand', dest="time_expand", nargs="+", type=float, metavar="DUR",
                        default=test_obj.time_expand, help="Length of time, in seconds, of extra"+
                        " audio to send to ABC_MRT16. Adding time protects against inaccurate M2E"+
                        " latency calculations and misaligned audio. A scalar value sets time"+
                        " expand before and after the keyword. A two element vector sets the"+
                        " time at the beginning and the end separately.")
    parser.add_argument('-b', '--blocksize', type=int, default=sim_obj.blocksize, metavar="SZ",
                        help="Block size for transmitting audio, must be a power of 2 "+
                        "(default: %(default)s).")
    parser.add_argument('-q', '--buffersize', type=int, default=sim_obj.buffersize, metavar="SZ",
                        help="Number of blocks used for buffering audio (default: %(default)s)")
    parser.add_argument('--overplay', type=float, default=sim_obj.overplay,metavar='DUR',
                        help='The number of seconds to play silence after the audio is complete'+
                        '. This allows for all of the audio to be recorded when there is delay'+
                        ' in the system')
    parser.add_argument('-d', '--outdir', default=test_obj.outdir, metavar="DIR",
                        help="Directory that is added to the output path for all files.")
    parser.add_argument('-i', '--sthresh', dest="s_thresh", default=test_obj.s_thresh,
                        help="The threshold of A-weight power for P2, in dB, below which a trial"+
                        " is considered to have no audio. (Defaults to %(default).1f dB)")
    parser.add_argument('-j', '--stries', dest="s_tries", type=int, default=test_obj.s_tries,
                        help="Number of times to retry the test before giving up. (Defaults to %(default)i)") 
    
    args = parser.parse_args()
    
    #-------------------[Recovery Data File Detection]--------------------
    
    # If data_file found then place into 'rec_file' dictionary
    if (args.data_file != ""):
        recover = True     # Boolean indicating recover file used
        test_obj.data_file = args.data_file
        with open(test_obj.data_file, "rb") as pkl:
            test_obj.rec_file = pickle.load(pkl)

    else:
        recover = False
        
    # Set instance variables as needed
    if recover:
        skippy = ['rec_file']
        # Instance variable setting function
        for k, v in test_obj.rec_file.items():
            if hasattr(test_obj, k) and (k not in skippy):
                setattr(test_obj, k, v)

    else:
        # Set Access object variables to terminal arguments
        for k, v in vars(args).items():
            if hasattr(test_obj, k):
                setattr(test_obj, k, v)

    if not recover:
        # Check user's parameters for value errors etc.
        test_obj.param_check()
        
    #---------------------[Set audio interface properties]---------------------

    test_obj.audio_interface.blocksize = args.blocksize
    test_obj.audio_interface.buffersize = args.buffersize
    test_obj.audio_interface.overplay = args.overplay
    
    #-----------------------[Open RadioInterface]-------------------------
    
    with RadioInterface(args.radioport) as test_obj.ri:
        
        #------------------------------[Get test info]------------------------------

        gui = mcvqoe.gui.TestInfoGui()
        
        gui.chk_audio_function = lambda : mcvqoe.hardware.single_play(
                                                    test_obj.ri,test_obj.audio_interface,
                                                    )
        
        #if recovering, re-use notes and things
        if (recover):
            gui.info_in['test_type'] = test_obj.info['test_type']
            gui.info_in['tx_dev'] = test_obj.info['tx_dev']
            gui.info_in['rx_dev'] = test_obj.info['rx_dev']
            gui.info_in['system'] = test_obj.info['system']
            gui.info_in['test_loc'] = test_obj.info['test_loc']
            gui.info_in['Pre Test Notes'] = test_obj.info['Pre Test Notes'] + \
                                          'Test restarted due to error\n'+ \
                                          f'Data loaded from : {args.data_file}\n'
                                          #TODO : add restarted trial number?
        
        test_obj.info = gui.show()

        #check if the user canceled
        if (test_obj.info is None):
            print(f"\n\tExited by user")
            sys.exit(1)
        
        #------------------------------[Run Test]------------------------------
        
        test_obj.run(recovery=recover)
    
if __name__ == "__main__":
    
    main()