#!/usr/bin/env python
import argparse
import mcvqoe.gui
import mcvqoe.hardware
import mcvqoe.simulation
import os.path
import sys

import numpy as np
import mcvqoe.gui.test_info_gui as test_info_gui

from .access_time import measure as access_time_meas
from .access_time_hw_test import int_or_inf
           
def main():

    #create sim object
    sim_obj = mcvqoe.simulation.QoEsim(
                    playback_chans = {'tx_voice':0, 'start_signal':1},
                    rec_chans = {'rx_voice':0, 'PTT_signal':1},
                    )

    # Create Access object
    test_obj = access_time_meas()
    #set wait times to zero for simulation
    test_obj.ptt_gap = 0
    #default trials to inf because we don't need to stop
    test_obj.trials = np.inf
    #only get test notes on error
    test_obj.get_post_notes = lambda : mcvqoe.gui.post_test(error_only=True)

    #set audioInterface to sim object
    test_obj.audio_interface = sim_obj
    #set radio interface object to sim object
    test_obj.ri = sim_obj

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
    parser.add_argument('-t', '--trials', type=int_or_inf, default=test_obj.trials, metavar="T",
                        help="Number of trials to use for test. Defaults to 100.")
    parser.add_argument('-y', '--pttdelay', nargs="+", dest="ptt_delay", type=float,
                        default=test_obj.ptt_delay, help="ptt_delay can be a 1 or 2 element double"+
                        " vector. If it is a 1 element vector then it specifies the minimum"+
                        " ptt_delay that will be used with the maximum being the end of the"+
                        " first word in the clip. If a two element vector then the first"+
                        " element is the smallest delay used and the second is the largest."+
                        " Defaults to 0.0(start of clip).")
    parser.add_argument('-p', '--pttstep', dest="ptt_step", type=float, default=test_obj.ptt_step,
                        help="Time in seconds between successive pttdelays. Default is 20ms.")
    parser.add_argument('-z', '--bgnoisefile', dest="bgnoise_file", default='', help="If this is"+
                        " non empty then it is used to read in a noise file to be mixed with the "+
                        "test audio. Default is no background noise.")
    parser.add_argument('-v', '--bgnoisevolume', dest="bgnoise_volume", type=float,
                        default=test_obj.bgnoise_volume, help="Scale factor for background"+
                        " noise. Defaults to 0.1.")
    parser.add_argument('-s', '--pttgap', dest="ptt_gap", type=float, default=test_obj.ptt_gap,
                        help="Time to pause after completing one trial and starting the next."+
                        " Defaults to 3.1s.")
    parser.add_argument('-e', '--pttrep', dest="ptt_rep", type=int, default=test_obj.ptt_rep,
                        help="Number of times to repeat a given PTT delay value. If auto_stop is "+
                        "used ptt_rep must be greater than 15.")
    parser.add_argument('-c', '--autostop', dest="auto_stop", action='store_true', default=test_obj.auto_stop,
                        help="Enable checking for access and stopping the test when it is detected.")
    parser.add_argument('--no-autostop', dest="auto_stop", action='store_false',
                        help="Disable checking for access and stopping the test when it is detected.")
    parser.add_argument('-f', '--stoprep', dest="stop_rep", type=int, default=test_obj.stop_rep,
                        help="Number of times that access must be detected in a row before the"+
                        " test is completed.")
    #QoEsim does not support simulation of device delay
    #TODO : update this if QoEsim is changed in the future
    parser.add_argument('-g', '--devdly', dest="dev_dly", type=float, default=0,
                        help="Delay in seconds of the audio path with no communication device"+
                        " present. Defaults to 21e-3.")
    parser.add_argument('-x', '--timeexpand', dest="time_expand", nargs="+", type=float, metavar="DUR",
                        default=test_obj.time_expand, help="Length of time, in seconds, of extra"+
                        " audio to send to ABC_MRT16. Adding time protects against inaccurate M2E"+
                        " latency calculations and misaligned audio. A scalar value sets time"+
                        " expand before and after the keyword. A two element vector sets the"+
                        " time at the beginning and the end separately.")
    parser.add_argument('--overplay', type=float, default=sim_obj.overplay, metavar='DUR',
                        help='The number of seconds to play silence after the audio is complete'+
                        '. This allows for all of the audio to be recorded when there is delay'+
                        ' in the system')
    parser.add_argument('-d', '--outdir', default=test_obj.outdir, metavar="DIR",
                        help="Directory that is added to the output path for all files.")
    parser.add_argument('-i', '--sthresh', dest="s_thresh", default=test_obj.s_thresh,
                        help="The threshold of A-weight power for P2, in dB, below which a trial"+
                        " is considered to have no audio. Defaults to -50.")
    parser.add_argument('-j', '--stries', dest="s_tries", type=int, default=test_obj.s_tries,
                        help="Number of times to retry the test before giving up. Defaults to 3.")    
    parser.add_argument('-P','--use-probabilityiser', default=False, dest='use_probabilityiser', action='store_true',
                        help='Use probabilityiesr to make channel "flaky"')
    parser.add_argument('--no-use-probabilityiser', dest='use_probabilityiser', action='store_false',
                        help='don\'t use probabilityiesr')
    parser.add_argument('--P-a1', dest='P_a1', type=float, default=1,
                        help='P_a1 for probabilityiesr')
    parser.add_argument('--P-a2', dest='P_a2', type=float, default=1,
                        help='P_a2 for probabilityiesr')
    parser.add_argument('--P-r', dest='P_r', type=float, default=1,
                        help='P_r for probabilityiesr')
    parser.add_argument('--P-interval', dest='pInterval', type=float, default=1,
                        help='Time interval for probabilityiesr in seconds')
    parser.add_argument('--channel-tech', default=sim_obj.channel_tech, metavar='TECH', dest='channel_tech',
                        help='Channel technology to simulate (default: %(default)s)')
    parser.add_argument('--channel-rate', default=sim_obj.channel_rate, metavar='RATE', dest='channel_rate',
                        help='Channel technology rate to simulate. Passing \'None\' will use the technology default. (default: %(default)s)')
    parser.add_argument('--channel-m2e', type=float, default=sim_obj.m2e_latency, metavar='L', dest='m2e_latency',
                        help='Channel mouth to ear latency, in seconds, to simulate. (default: %(default)s)')
    parser.add_argument('--channel-access', type=float, metavar='D', 
                        default=sim_obj.access_delay, dest='access_delay',
                        help='Channel access time, in seconds, to simulate. '+
                        '(default: %(default)s)')
    
    args = parser.parse_args()
    
    #-------------------[Recovery Data File Detection]--------------------
 
    # Set Access object variables to terminal arguments
    for k, v in vars(args).items():
        if hasattr(test_obj, k):
            setattr(test_obj, k, v)

    # Check user's parameters for value errors etc.
    test_obj.param_check()
        
    #-------------------------[Set simulation settings]-------------------------

    sim_obj.channel_tech = args.channel_tech
    
    sim_obj.overplay = args.overplay
    
    #set channel rate, check for None
    if (args.channel_rate == 'None'):
        sim_obj.channel_rate = None
    else:
        sim_obj.channel_rate = args.channel_rate
        
    sim_obj.m2e_latency = args.m2e_latency
    sim_obj.access_delay = args.access_delay
    
    #------------------------------[Get test info]------------------------------
    
    gui = mcvqoe.gui.TestInfoGui(write_test_info=False)
    
    gui.chk_audio_function = lambda : mcvqoe.hardware.single_play(sim_obj,sim_obj,
                                                    playback=True,
                                                    ptt_wait=0)

    #construct string for system name
    system = sim_obj.channel_tech
    if (sim_obj.channel_rate is not None):
        system += ' at ' + str(sim_obj.channel_rate)

    gui.info_in['test_type'] = "simulation"
    gui.info_in['tx_dev'] = "none"
    gui.info_in['rx_dev'] = "none"
    gui.info_in['system'] = system
    gui.info_in['test_loc'] = "N/A"
    test_obj.info = gui.show()

    #check if the user canceled
    if (test_obj.info is None):
        print(f"\n\tExited by user")
        sys.exit(1)
    
    #-----------------------[Add simulation info to log]-----------------------
    
    test_obj.info['sim m2e'] = sim_obj.m2e_latency
    test_obj.info['sim acc'] = sim_obj.access_delay
    
    #--------------------------------[Run Test]--------------------------------
    
    test_obj.run(recovery=False)
    
if __name__ == "__main__":
    
    main()