#!/usr/bin/env python
import abcmrt
import argparse
import csv
import datetime
import mcvqoe
import os
import pickle
import scipy.interpolate
import scipy.io.wavfile
import scipy.signal
import sys
import time
import timeit

from fractions import Fraction
from mcvqoe.hardware import AudioPlayer
from mcvqoe.math import approx_permutation_test
from mcvqoe.hardware import RadioInterface
from warnings import warn

import mcvqoe.gui.test_info_gui as test_info_gui
import numpy as np
import tkinter as tk
        
def int_or_inf(input):
    """Check for 'infinite' entry, and change 'trials' to np.inf if found"""
    try:
        return int(input)
    except ValueError:
        word = input.lower()
        infinite = ['inf', 'np.inf', 'math.inf', 'infinite']
        if word in infinite:
            return np.inf
        else:
            print(f"\n{input} is an invalid value for '-t/--trials'")
            sys.exit(1)

#TODO : maybe we should put this in abcmrt?    
#abcmrt only works with 48 kHz audio
fs_abcmrt=48000

def chans_to_string(chans):
    #channel string
    return '('+(';'.join(chans))+')'
    
def trial_limit_batt_check(check=False):
    """Trial limit reached gui, and user_pause from retry function"""
    
    # Window creation
    global root
    root = tk.Tk()
    root.geometry('500x500')
    # Button frame for easy centering
    button_frame = tk.Frame(root)
    button_frame.pack(expand=True)
    
    # Check boolean for different messages
    if check:
        root.title("User Pause")
        label = tk.Label(button_frame, text="Check connections/radios and press"+
                         " Enter to continue")
        label.grid(column=0, row=0)
    else:
        root.title("Trial Limit")
        label = tk.Label(button_frame, text="Trial limit reached. Check batteries"+
                         " and press Enter to continue")
        label.grid(column=0, row=0)
        
    button = tk.Button(button_frame, text="Enter", command=root.destroy)
    button.grid(column=0, row=1)
    root.mainloop()

def mk_format(header):
    
    fmt=""
    
    for col in header:
        #split at first space
        col=col.split()[0]
        #remove special chars
        col=''.join(c for c in col if c.isalnum())
        #need to not use special names
        #TODO : should this be done better?
        if(col=='try'):
            col='rtry'
        
        fmt+='{'+col+'},'
    #replace trailing ',' with newline
    fmt=fmt[:-1]+'\n'
    
    return fmt
    
class measure:
    
    data_header=['PTT_time','PTT_start','ptt_st_dly','P1_Int','P2_Int',
                 'm2e_latency','channels','TimeStart','TimeEnd','TimeGap']
    
    bad_header=['FileName','trial_count','clip_count','try#','p2A-weight',
                'm2e_latency','channels','TimeStart','TimeEnd','TimeGap']
    
    def __init__(self):
        
        self.audio_files = []
        self.audio_path = ""
        self.audio_interface = None
        self.auto_stop = False
        self.bgnoise_file = ""
        self.bgnoise_volume = 0.1
        self.data_file = ""
        self.dev_dly = float(31e-3)
        self.get_post_notes = None
        self.info = {}
        self.inter_word_diff = 0.0 # Used to compare inter word delays
        self.no_log = ('test', 'ri')
        self.outdir = ""
        self.ptt_delay = [0.0]
        self.ptt_gap = 3.1
        self.ptt_rep = 30
        self.ptt_step = float(20e-3)
        self.rec_file = None
        self.ri = None
        self.user_check= trial_limit_batt_check
        self.s_thresh = -50
        self.s_tries = 3
        self.stop_rep = 10
        # TODO: warn if first time_expand is too small, talk about in class documentation
        self.time_expand = [100e-3 - 0.11e-3, 0.11e-3]
        self.trials = 100.0

    def _cutpoint_check(self, cutpoint):
        """Check if cutpoint contains what we need and has the proper format"""

        with open(cutpoint, 'r') as csv_file:
            reader = csv.reader(csv_file)
            rows = sum(1 for row in reader)
            if (rows != 5):
                raise ValueError(f"Loading {cutpoint}: 4 'words' expected but, {rows-1} found")
            
            sheet = list(csv.reader(open(cutpoint)))
            if (sheet[1][0] != 'NaN') or (sheet[3][0] != 'NaN'):
                raise ValueError(f"Loading {cutpoint}: Words 1 and 3 must be silence")
            
            if (sheet[2][0] != sheet[4][0]):
                raise ValueError(f"Loading {cutpoint}: Words 2 and 4 must be the same")
            
            # Check inter word delays
            inter_delay = (int(sheet[3][2]) - int(sheet[3][1])) / self.audio_interface.sample_rate
            if (self.inter_word_diff == 0.0):
                self.inter_word_diff = inter_delay
            else:
                if (self.inter_word_diff != inter_delay):
                    warn(f"It is recommended that all inter word times are the same\n")

    def _cutpoint_exist(self, audiofile):
        """Check if there's a cutpoint to match the audio file
        
        ...
        
        Parameters
        ----------
        audiofile : str
            The .wav file we're hoping to find a match for
            
        Returns
        -------
        found : boolean
            True/False if cutpoint is found/not found
            
        """
        
        # Split name of file with file extension
        name, extension = os.path.splitext(audiofile)
        cutpoint = name + ".csv"
        if os.path.isfile(cutpoint):
            return cutpoint
        else:
            return None

    def run(self, recovery=False):
        """Run an Access Time test
        
        ...
        
        Parameters
        ----------
        recovery : Boolean
            Is this a recovery from a previous test?
        
        """
        
        #----------------[List of Vars to Save in Pickle File]----------------
        
        save_vars = ('audiofiles_names', 'cutpoints', 'clipnames', 'audiofiles',
                     'bad_name', 'temp_data_filenames', 'ptt_st_dly',
                     'wav_cap_dir')
        
        # Array of audiofile full path names
        audiofiles_names = []
        # Array of cutpoint tuples
        cutpoints = []
        # Array of cutpoint/audiofile names (no path or extensions)
        clipnames = []
        # Array of resampled audiofiles
        audiofiles = []
        
        # Initialize clip end time for gap time calculation
        time_e = np.nan
        tg_e = np.nan
        
        #-----------------------[Check audio sample rate]-----------------------
        
        if(self.audio_interface.sample_rate != fs_abcmrt):
            raise ValueError(f'audio_interface sample rate is {self.audio_interface.sample_rate} Hz but only {fs_abcmrt} Hz is supported')
        
        #------------------[Check for correct audio channels]------------------
        
        if('tx_voice' not in self.audio_interface.playback_chans.keys()):
            raise ValueError('self.audio_interface must be set up to play tx_voice')
        if('start_signal' not in self.audio_interface.playback_chans.keys()):
            raise ValueError('self.audio_interface must be set up to play start_signal')
            
        if('rx_voice' not in self.audio_interface.rec_chans.keys()):
            raise ValueError('self.audio_interface must be set up to record rx_voice')
        if('PTT_signal' not in self.audio_interface.rec_chans.keys()):
            raise ValueError('self.audio_interface must be set up to record PTT_signal')
                   
        #---------------------[Generate csv format strings]---------------------
        
        dat_format=mk_format(self.data_header)
        bad_format=mk_format(self.bad_header)
        
        #------------------[Load In Old Data File If Given]-------------------
        
        if recovery:
            
            trial_count = 0
            
            # Copy recovery variables to current test
            ptt_st_dly = self.rec_file['ptt_st_dly']
            audiofiles_names = self.rec_file['audiofiles_names']
            clipnames = self.rec_file['clipnames']
            cutpoints = self.rec_file['cutpoints']
            audiofiles = self.rec_file['audiofiles']
            
            # Recreate 'temp_data_filenames'
            temp_data_filenames = self.rec_file['temp_data_filenames']
            # Boolean array to see which files to copy to new name
            copy_files = np.full(len(temp_data_filenames), False)
            # Save old names to copy to new names
            old_filenames = temp_data_filenames
            # Save old .wav folder
            old_wavdir = self.rec_file['wav_cap_dir']
            # Save old bad file name
            old_bad_name = self.rec_file['bad_name']
   
            for k in range(len(temp_data_filenames)):
                save_dat = self.load_dat(temp_data_filenames[k])
                if not save_dat:
                    print(f"\nNo data file found for {temp_data_filenames[k]}\n")
                else:
                    # File is good, need to copy to new name
                    copy_files[k] = True
                    # Get number of "rows" from CSV
                    clen = len(save_dat)
                    # Initialize success with zeros
                    success = np.zeros((2, (len(ptt_st_dly[k])*self.ptt_rep)))
                    # Fill in success from file
                    for p in range(clen):
                        success[0, p] = save_dat[p]['P1_Int']
                        success[1, p] = save_dat[p]['P2_Int']
                    # Stop flag is computed every delay step
                    stop_flag = np.empty(len(ptt_st_dly[k]))
                    stop_flag[:] = np.nan
                    # Trial count is the sum of all trial counts from each file
                    trial_count = trial_count + clen
                    # Set clip start to curren index
                    # If another datafile is found it will be overwritten
                    clip_start = k
                    # Initialize k_start
                    k_start = 0
                    
                    # Loop through data and evaluate stop condition
                    for kk in range(self.ptt_rep, clen, self.ptt_rep):
                        
                        # Identify trials calculated at last timestep
                        ts_ix = np.arange((kk-(self.ptt_rep)), kk)
                        p1_intell = success[0, ts_ix]
                        p2_intell = success[1, :]
                        stop_flag[k] = not approx_permutation_test(p2_intell, p1_intell, tail = 'right')
                        k_start = k_start + 1
                    
                    # Assign kk_start point for inner loop    
                    if (clen==0):
                        kk_start = 0
                    else:
                        kk_start = ((clen-1) % self.ptt_rep) + 1
        
        #-------[Parse Through Audio Files/Cutpoints and Perform Checks]--------
        
        # Only read in data if this is the first time
        else:
        
            # Set initial loop indices
            clip_start = 0
            k_start = 0
            kk_start = 0
            
            # Parse through given audio_files
            for aud in self.audio_files:
                
                # Create audio file path name
                audio = os.path.join(self.audio_path, aud)
                    
                # Check if file exists, and run cutpoint checks
                if os.path.isfile(audio):
                    cutpoint = self._cutpoint_exist(audio)
                    if cutpoint is not None:
                        audiofiles_names.append(audio)
                        
                        self._cutpoint_check(cutpoint)
                        # Turn cutpoint file path into useable tuple
                        cut = mcvqoe.load_cp(cutpoint)
                        cutpoints.append(cut)
                        
                        # Add to clipnames
                        tmp_clip = os.path.basename(audio)
                        nm, _ = os.path.splitext(tmp_clip)
                        
                        clipnames.append(nm)
                    else:
                        raise ValueError(f"{audio} has no corresponding .csv cutpoints file!")
                else:
                    raise TypeError(f"\n{audio} is not an audio file!")
            
            # Check proper sample rate and place audio files into array
            for aud in audiofiles_names:
                fs_file, audio_dat = scipy.io.wavfile.read(aud)
                if fs_file != fs_abcmrt:
                    raise ValueError(f"\nImproper sample rate. {aud} is at {fs_file} Hz and {fs_abcmrt} Hz is expected")
                audio = mcvqoe.audio_float(audio_dat)
                audiofiles.append(audio)
            
            # If noise file was given, resample to match audio files
            if (self.bgnoise_file):
                nfs, nf = scipy.io.wavfile.read(self.bgnoise_file)
                rs = Fraction(fs_abcmrt/nfs)
                nf = mcvqoe.audio_float(nf)
                nf = scipy.signal.resample_poly(nf, rs.numerator, rs.denominator)    

        
        #-------------------------[Get Test Start Time]-------------------------
        self.info['Tstart']=datetime.datetime.now()
        dtn=self.info['Tstart'].strftime('%d-%b-%Y_%H-%M-%S')
        
        #--------------------------[Fill log entries]--------------------------
        #set test name
        self.info['test']='Access'
        #add abcmrt version
        self.info['abcmrt version']=abcmrt.version
        #fill in standard stuff
        self.info.update(mcvqoe.write_log.fill_log(self))

        #-----------------[Initialize Folders and Filenames]------------------

        # Data folder
        dat_fold = os.path.join(self.outdir, "data")
        os.makedirs(dat_fold, exist_ok=True)
        
        # Recovery folder
        rec_fold = os.path.join(dat_fold, 'recovery')
        os.makedirs(rec_fold, exist_ok=True)
        
        # Error folder
        err_fold = os.path.join(dat_fold, 'error')
        os.makedirs(err_fold, exist_ok=True)
        
        # CSV file folder
        csvdir = os.path.join(dat_fold, "csv")
        os.makedirs(csvdir, exist_ok=True)
        
        # WAV file folder
        wavdir = os.path.join(dat_fold, "wav")
        os.makedirs(wavdir, exist_ok=True)
        
        # Create capture WAV file folder
        td = self.info.get("Tstart").strftime("%d-%b-%Y_%H-%M-%S")
        wav_cap_dir = 'capture_' + self.info['Test Type'] + '_' + td
        wav_cap_dir = os.path.join(wavdir, wav_cap_dir)
        # Expectation is this does not exist
        os.makedirs(wav_cap_dir, exist_ok=False)
        
        # Generate csv filenames and add path
        self.data_filenames = []
        temp_data_filenames = []
        for name in clipnames:
            file = f"capture_{self.info['Test Type']}_{td}_{name}.csv"
            tmp_f = f"capture_{self.info['Test Type']}_{td}_{name}_TEMP.csv"
            file = os.path.join(csvdir, file)
            tmp_f = os.path.join(csvdir, tmp_f)
            self.data_filenames.append(file)
            temp_data_filenames.append(tmp_f)

        # Generate filename for bad csv data
        bad_name = f"capture_{self.info['test']}_{td}_BAD.csv"
        bad_name = os.path.join(csvdir, bad_name)
        
        #---------------------[Add Noise File if Given]-----------------------
        
        if (self.bgnoise_file):
            for audio in range(len(audiofiles)):
                if (nf.size != audiofiles[audio].size):
                    nf = np.resize(nf, audiofiles[audio].size)
                audiofiles[audio] = audiofiles[audio] + nf*self.bgnoise_volume

        #---------[Write Transmit Audio File(s) and cutpoint File(s)]----------
        
        for num in range(len(audiofiles_names)):
            tmp_csv = "Tx_" + clipnames[num] + ".csv"
            tmp_wav = "Tx_" + clipnames[num] + ".wav"
            tmp_csv = os.path.join(wav_cap_dir, tmp_csv)
            tmp_wav = os.path.join(wav_cap_dir, tmp_wav)
            mcvqoe.write_cp(tmp_csv, cutpoints[num])
            # Write audio file
            scipy.io.wavfile.write(tmp_wav,self.audio_interface.sample_rate,audiofiles[num])

        #-------------------[Generate Filters and Times]----------------------

        # Calculate niquest frequency
        fn = self.audio_interface.sample_rate/2
        
        # Create lowpass filter for PTT signal processing
        ptt_filt = scipy.signal.firwin(400, 200/fn, pass_zero='lowpass')
        
        # Generate time vector for audiofiles
        t_y = []
        for i in range(len(audiofiles)):
            t_y.append((np.arange(1, len(audiofiles[i])+1)) / self.audio_interface.sample_rate)

        #-----------------------[Generate PTT Delays]-------------------------
        
        if not recovery:
        
            ptt_st_dly = []
    
            if (len(self.ptt_delay) == 1):
                for num in range(len(cutpoints)):
                    # Word start time from end of first silence
                    w_st = (cutpoints[num][0]['End']/self.audio_interface.sample_rate)
                    # Word end time from end of word
                    w_end = (cutpoints[num][1]['End']/self.audio_interface.sample_rate)
                    # Delay during word (.0001 added to w_end ensures w_end's use)
                    w_dly = np.arange(w_st, (w_end+.0001), self.ptt_step)
                    # Delay during silence (.0001 decrement to ensure ptt_delay usage)
                    s_dly = np.arange(w_st, (self.ptt_delay[0]-.0001), -self.ptt_step)
                    # Generate delay from word delay and silence delay
                    # Word delay must be reversed
                    ptt_st_dly.append(np.concatenate((w_dly[::-1], s_dly[1:])))
                    # Ensure that final delay time will not be negative
                    if(ptt_st_dly[-1][-1] < 0.0):
                        ptt_st_dly[-1][-1] = 0.0
    
            else:
                for _ in range(len(cutpoints)):
                    dly_steps = np.arange(self.ptt_delay[1], self.ptt_delay[0], -self.ptt_step)
                    ptt_st_dly.append(dly_steps)
    
            # Running count of the number of completed trials
            trial_count = 0

        #----------------[Pickle important data for restart]------------------
        
        # Initialize error file
        error_file = os.path.join(rec_fold, td+'.pickle')
         
        # Error dictionary
        err_dict = {}
         
        for var in save_vars:
            err_dict[var] = locals()[var]
         
        # Add all access_time object parameters to error dictionary
        for i in self.__dict__:
            skip = ['no_log', 'audio_interface', 'ri',
                    'inter_word_diff', 'get_post_notes']
            if (i not in skip):
                err_dict[i] = self.__dict__[i]
         
        # Place dictionary into pickle file
        with open(error_file, 'wb') as pkl:
            pickle.dump(err_dict, pkl)
            
        #---------------------------[write log entry]---------------------------
        
        mcvqoe.write_log.pre(info=self.info, outdir=self.outdir)

        #-----------------------[Notify User of Start]------------------------
        
        # Turn on LED
        self.ri.led(1, True)
    
        try:
    
            #---------------------[Save Time for Set Timing]----------------------
            
            set_start = datetime.datetime.now().replace(microsecond=0)
    
            #----------------------------[Clip Loop]------------------------------
            
            for clip in range(len(audiofiles)):
                
                #---------------------[Calculate Delay Start Index]-------------------
                
                # Calculate index to start M2E latency at. This is 3/4 through the second silence.
                # If more of the clip is used, ITS_delay can get confused and return bad values.
                dly_st_idx = (int(cutpoints[clip][2]['Start'] + 0.75*(cutpoints[clip][2]['End']
                                                                      -cutpoints[clip][2]['Start'])))
                
                # Check if file is not present (not a restart)
                if (True):
                    
                    #-------------------------[Write CSV Header]--------------------------
                    
                    with open(temp_data_filenames[clip], 'w', newline='') as csv_file:
                        writer = csv.writer(csv_file)
                        writer.writerow([f'Audiofile = {audiofiles_names[clip]}'])
                        writer.writerow([f'fs = {self.audio_interface.sample_rate}'])
                        writer.writerow(['----------------'])
                        writer.writerow(self.data_header)
                    
                    # Print name and location of datafile    
                    print(f"\nStarting {clipnames[clip]}\nStoring data in:\n\t'"+
                          f"{temp_data_filenames[clip]}'\n")
                    
                    #-----------------------------[Stop Flag]-----------------------------
                    
                    success = np.zeros((2, (len(ptt_st_dly[clip])*self.ptt_rep)))

                    # Stop flag is computed every delay step
                    stop_flag = np.empty(len(ptt_st_dly[clip]))
                    stop_flag[:] = np.nan
                    
                    # Initialize clip count
                    clip_count = 0
                
                #--------------------------[Delay Step Loop]--------------------------
                
                for k in range(k_start, len(ptt_st_dly[clip])):
                    
                    #-------------------[Print Current Clip and Delay]--------------------
                    
                    print(f"Delay : {ptt_st_dly[clip][k]}s\n Clip : {clipnames[clip]}\n", flush=True)
                    
                    #-------------------------[Measurement Loop]--------------------------
                    
                    for kk in range(kk_start, self.ptt_rep):
                        
                        #-----------------------[Increment Trial Count]-----------------------
                        
                        trial_count = trial_count + 1
                        
                        #------------------------[Increment Clip Count]-----------------------
                        
                        clip_count = clip_count + 1
                        
                        #-----------------------------[Check Loop]----------------------------
                        
                        # A-weight power of P2, used for silence detection
                        a_p2 = -np.inf
                        
                        # Number of retries for this clip
                        retries = 0
                        
                        while (a_p2 <= self.s_thresh):
                            
                            retries = retries + 1
                            
                            # Check if we've exceded retry limit
                            if (retries > self.s_tries):
                                
                                # Turn on LED when waiting for user input
                                self.ri.led(2, True)
                                # Inform user of problem
                                warn("Audio not detected through the system.")
                                # TODO Check if we have retry function
                                self.user_check(check=True)
                                
                                # Turn off LED, resuming
                                self.ri.led(2, False)
                                
                            #---------------------[Key Radio and Play Audio]----------------------

                            # Setup the push to talk to trigger
                            self.ri.ptt_delay(ptt_st_dly[clip][k], use_signal=True)
                            
                            # Save end time of previous clip
                            time_last = time_e
                            tg_last = tg_e
                            
                            # Create audiofile name/path for recording
                            audioname = f"Rx{clip_count}_{clipnames[clip]}.wav"
                            audioname = os.path.join(wav_cap_dir, audioname)
                            
                            # Get start timestamp
                            time_s = datetime.datetime.now().replace(microsecond=0)
                            tg_s = timeit.default_timer()
                            
                            # Play and record audio data
                            rec_names = self.audio_interface.play_record(audiofiles[clip], audioname)
                            
                            # Get start time
                            time_e = datetime.datetime.now().replace(microsecond=0)
                            tg_e = timeit.default_timer()
                            
                            # Get the wait state from radio interface
                            state = self.ri.waitState()
                            
                            # Depress the push to talk button
                            self.ri.ptt(False, num=1)
                            
                            # Check wait state to see if PTT was triggered properly
                            if (state == 'Idle'):
                                # Everything is good, do nothing
                                pass
                            elif (state == 'Signal Wait'):
                                # Still waiting for start signal, give error
                                raise RuntimeError(f"Radio interface did not receive the start signal."+
                                                   " Check connections and output levels.")
                            elif (state == 'Delay'):
                                # Still waiting for delay time to expire, give warning
                                warn(f"PTT Delay longer than clip")
                            else:
                                # Unknown state
                                raise RuntimeError(f"Unknown radio interface wait state: {state}")
                            
                            # Calculate gap time (try/except here for nan exception)
                            try:
                                time_gap = tg_s - tg_last
                            except:
                                time_gap = np.nan

                            #------------------------[Pause Between Runs]-------------------------
                            
                            time.sleep(self.ptt_gap)
                            
                            #-------------------------[Data Processing]---------------------------
                            
                            #get index of rx_voice channel
                            voice_idx=rec_names.index('rx_voice')
                            #get index of PTT_signal
                            psig_idx=rec_names.index('PTT_signal')
                            
                            # Get latest run Rx audio
                            dat_fs, dat = scipy.io.wavfile.read(audioname)
                            dat = mcvqoe.audio_float(dat)
                            
                            # Extract push to talk signal (getting envelope)
                            ptt_sig = scipy.signal.filtfilt(
                                                ptt_filt,
                                                1,
                                                np.absolute(dat[:,psig_idx])
                                            )

                            # Get max value
                            ptt_max = np.amax(ptt_sig)
                            
                            # Check levels
                            if(ptt_max < 0.25):
                                warn('Low PTT signal values. Check levels')
                                
                            # Normalize levels
                            ptt_sig = ((ptt_sig*np.sqrt(2))/ptt_max)
                            
                            try:
                                # Determine turn on sample
                                ptt_st_idx = np.nonzero(ptt_sig > 0.5)[0][0]
                                
                                # Convert sample index to time
                                st = ptt_st_idx/self.audio_interface.sample_rate
                                
                            except IndexError:
                                st = np.nan
                                #TODO figure and plot like MATLAB
                            
                            # Find when the ptt was pushed    
                            ptt_start = st
                            
                            # Get ptt time. Subtract nominal play/record delay
                            # TODO: This might not be right, seems that device delays don't impact this
                            # (can be seen in PTT Gate data)
                            ptt_time = ptt_start - self.dev_dly
                            
                            # Calculate delay. Only use data after dly_st_idx
                            (_,dly_its) = mcvqoe.ITS_delay_est(
                                audiofiles[clip][dly_st_idx:], 
                                dat[dly_st_idx:,voice_idx],
                                mode='f',
                                dlyBounds=[0, np.inf],
                                fs=self.audio_interface.sample_rate
                            )
                            
                            #convert to seconds
                            dly_its=dly_its/self.audio_interface.sample_rate
                            
                            # Interpolate for new time
                            # TODO: do this with an offset once we've confirmed we're equivalent to matlab
                            inter_arr = (np.arange(len(dat[:, voice_idx]))/self.audio_interface.sample_rate-dly_its)
                            rec_int = scipy.interpolate.RegularGridInterpolator((inter_arr, ), dat[:,voice_idx])

                            # New shifted version of signal
                            rec_a = rec_int(t_y[clip])
            
                            # Expand cutpoints by TimeExpand
                            ex_cp_1 = np.array([cutpoints[clip][1]['Start'], cutpoints[clip][1]['End']])
                            ex_cp_2 = np.array([cutpoints[clip][3]['Start'], cutpoints[clip][3]['End']])
                            # Turn into numpy array for easier use
                            tm_expand = np.array(self.time_expand)
                            tm_expand = np.round((tm_expand*self.audio_interface.sample_rate) * np.array([1, -1]), 0)
                            tm_expand = tm_expand.astype(int)
                            ex_cp_1 = ex_cp_1 - tm_expand
                            ex_cp_2 = ex_cp_2 - tm_expand
                            
                            # Limit cutpoints to clip length
                            ylen = len(audiofiles[clip])
                            ex_cp_1[ex_cp_1>ylen] = ylen
                            ex_cp_2[ex_cp_2>ylen] = ylen
                            
                            # Minimum cutpoint index is 0
                            ex_cp_1[ex_cp_1<1] = 0
                            ex_cp_2[ex_cp_2<1] = 0
                            
                            # Split file into clips
                            dec_sp = [np.transpose(rec_a[ex_cp_1[0]: ex_cp_1[1]]),
                                      np.transpose(rec_a[ex_cp_2[0]: ex_cp_2[1]])]

                            # Compute MRT scores for clips
                            cutpoint_MRT = [cutpoints[clip][1]['Clip'], cutpoints[clip][3]['Clip']]
                            _, success[:, clip_count-1] = abcmrt.process(dec_sp, cutpoint_MRT)
                            
                            #----------------------[Calculate A-weight of P2]---------------------
                            
                            # Format time_gap for CSV file
                            if np.isnan(time_gap):
                                tg_str = 'nan'
                            else:
                                tg_str = f"{(time_gap//3600):.0f}:{((time_gap//60)%60):.0f}:{(time_gap%60):.3f}"
                            
                            a_p2 = mcvqoe.a_weighted_power(dec_sp[1], self.audio_interface.sample_rate)
                            
                            if (a_p2 <= self.s_thresh):
                                warn(f"A-weight power for P2 is {a_p2:.2f}dB\n")
                                
                                # Save bad audiofile
                                wav_name = f"Bad{clip_count}_r{retries}_{clipnames[clip]}"
                                wav_name = os.path.join(wav_cap_dir, wav_name)
                                #rename file to save it and record again
                                os.rename(audioname, wav_name)
                                
                                print(f"Saving bad data to '{bad_name}'\n")
                                # Check if file exists for appending, or we need to create it
                                if not (os.path.isfile(bad_name)):
                                    # File doesn't exist, create and write header
                                    with open(bad_name, 'w', newline='') as csv_file:
                                        writer = csv.writer(csv_file)
                                        writer.writerow(self.bad_header)
                                
                                # append with bad data
                                with open(bad_name, 'a') as csv_file:
                                    csv_file.write(
                                        bad_format.format(
                                            FileName=wav_name,
                                            trialcount=trial_count,
                                            clipcount=clip_count,
                                            rtry=retries,
                                            p2Aweight=a_p2,
                                            m2elatency=dly_its,
                                            channels=chans_to_string(rec_names),
                                            TimeStart=time_s.strftime('%H:%M:%S'),
                                            TimeEnd=time_e.strftime('%H:%M:%S'),
                                            TimeGap=tg_str
                                        )
                                    )
                                    
                        #--------------------------[End Check Loop]---------------------------
                        
                        #----------------------[Inform User of Restart]-----------------------
                        
                        # Check if it took more than one try
                        if(retries > 1):
                            # Print message that test is continuing
                            print(f"A-weight power of {a_p2:.2f} dB for P2. Continuing test\n", flush=True)
                            
                        #-------------------------[Save Trial Data]---------------------------
                        
                        with open(temp_data_filenames[clip], 'a') as csv_file:
                            csv_file.write(
                                dat_format.format(
                                    PTTtime=ptt_time,
                                    PTTstart=ptt_start,
                                    pttstdly=ptt_st_dly[clip][k],
                                    P1Int=success[0, clip_count],
                                    P2Int=success[1, clip_count],
                                    m2elatency=dly_its,
                                    channels=chans_to_string(rec_names),
                                    TimeStart=time_s.strftime('%H:%M:%S'),
                                    TimeEnd=time_e.strftime('%H:%M:%S'),
                                    TimeGap=tg_str
                                )
                            )
                        
                        #------------------------[Check Trial Limit]--------------------------
                        
                        if ((trial_count % self.trials) == 0):
                            
                            # Calculate set time
                            time_diff = datetime.datetime.now().replace(microsecond=0)
                            set_time = time_diff - set_start
                            
                            # Print set time
                            print(f"Time for {self.trials} trials : {set_time}")
                            
                            # Turn on LED when waiting for user input
                            self.ri.led(2, True)
                            
                            # wait for user
                            self.user_check()
                            
                            # Turn off LED, resuming
                            self.ri.led(2, False)
                            
                            # Save time for next set
                            set_start = datetime.datetime.now().replace(microsecond=0)
                            
                    #-----------------------[End Measurement Loop]------------------------
                    
                    # Reset start index so we start at the beginning
                    kk_start = 0
                    
                    #---------------------[Check Stopping Condition]----------------------
                     
                    # Identify trials calculated at last timestep ptt_st_dly[k]
                    ts_ix = np.arange((clip_count-(self.ptt_rep)), clip_count)
                     
                    # P1 intelligibility for last time step
                    p1_intell = success[0, ts_ix]
                    # All observed P2 intelligibility
                    p2_intell = success[1, :clip_count]
                     
                    # Perform approx permutation test to see if p1 intell is equivalent to p2 intell
                    # Null hypothesis is that they are the same
                    # Returns True if the null hypothesis is rejected (they are not the same)
                    # Returns False if the null hypothesis is not rejected (they are the same)
                    # Compares value mean(p2_intell) - mean(p1_intell)
                    # If P1 is not at asymptotic intell, this will be much larger than any repetitions
                    # in the approx_perm_test.
                    # If P1 is at asymptotic intell, this will be closish to 0, and well represented
                    # in repetitions in approx_perm_test.
                    # Thus, we put all the weight of our test on the right tail of the resample distribution.
                    # TODO: Had interesting discussion on if this would be better off being tail = 'two'.
                    # TODO: Revisit after validated equivalent results.
                    stop_flag[k] = not approx_permutation_test(p2_intell, p1_intell, tail = 'right')
                     
                    # Check if we should look for stopping condition
                    # Only stop if ptt delay is before the first word
                    if (self.auto_stop and (cutpoints[clip][1]['End']/self.audio_interface.sample_rate)>ptt_st_dly[clip][k]):
                        if (self.stop_rep<=k and all(stop_flag[(k-self.stop_rep):k])):
                            # If stopping condition met, break from loop
                            break
                #-----------------------[End Delay Step Loop]-------------------------
                
                # Reset start index so we start at the beginning
                k_start = 0
            
            #--------------------------[End Clip Loop]----------------------------
            
            #--------------------[Change Name of Data Files]----------------------
            
            for k in range(len(temp_data_filenames)):
                print(f"\nRenaming '{temp_data_filenames[k]}' to '{self.data_filenames[k]}'")
                os.rename(temp_data_filenames[k], self.data_filenames[k])
        finally:
            if(self.get_post_notes):
                #get notes
                info=self.get_post_notes()
            else:
                info={}
            #finish log entry
            mcvqoe.post(outdir=self.outdir,info=info)

            
    def param_check(self):
        """Check all input parameters for value errors"""
        
        if ((self.auto_stop) and (self.ptt_rep < 16)):
            raise ValueError(f"ptt_rep must be greater than 15 if autostop is used.\n"+
                             f"ptt_rep set to {self.ptt_rep}")
        
        # Time expand check and resize if necessary
        if (len(self.time_expand) < 1):
            raise ValueError(f"Time expand must be more at least one variable")
        if (len(self.time_expand) > 2):
            warn(f"Time expand can only be a maximum of two variables\n")
            self.time_expand = self.time_expand[:2]

        # Check if given audio path exists
        if (self.audio_path != ""):
            if os.path.isdir(self.audio_path) is False:
                raise ValueError(f"Audio path ({self.audio_path}) not found.")
                
    def load_dat(self,fname):
        """Load data from CSV file and skip header
        
        ...
        
        Parameters
        ----------
        fname : csv file path
            csv file to be loaded into dictionary list
            
        Returns
        -------
        dat_list : List
            List of dictionaries containing row data(header skipped)
        
        """

        # List to store each csv row(dictionaries)
        dat_list = []
        
        # Read csv file and occupy list, skipping header section
        with open(fname) as csv_f:
            reader = csv.DictReader(csv_f, fieldnames=self.data_header)
            for n, row in enumerate(reader):
                if n < 4:
                    continue
                dat_list.append(row)
                
            # Delete last row to ensure proper restart
            del dat_list[-1]

            return dat_list
           
def main():
    
    # Create Access object
    test_obj = measure()
    # Set post test notes function
    test_obj.get_post_notes = test_info_gui.post_test
    
    #--------------------[Create AudioPlayer Object]----------------------
        
    ap = AudioPlayer(
                    playback_chans = {'tx_voice':0, 'start_signal':1},
                    rec_chans = {'rx_voice':0, 'PTT_signal':1},
                    )
                    
    test_obj.audio_interface = ap

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
    parser.add_argument('-r', '--radioport', default='', metavar="PORT",
                        help="Port to use for radio interface. Defaults to the first"+
                        " port where a radio interface is detected.")
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
    parser.add_argument('-g', '--devdly', dest="dev_dly", type=float, default=test_obj.dev_dly,
                        help="Delay in seconds of the audio path with no communication device"+
                        " present. Defaults to 21e-3.")
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
    parser.add_argument('-b', '--blocksize', type=int, default=ap.blocksize, metavar="SZ",
                        help="Block size for transmitting audio, must be a power of 2 "+
                        "(default: %(default)s).")
    parser.add_argument('-q', '--buffersize', type=int, default=ap.buffersize, metavar="SZ",
                        help="Number of blocks used for buffering audio (default: %(default)s)")
    parser.add_argument('--overplay', type=float, default=ap.overplay,metavar='DUR',
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
    test_obj.audio_interface.blocksize=args.blocksize
    test_obj.audio_interface.buffersize=args.buffersize
    test_obj.audio_interface.overplay=args.overplay
    
    #-----------------------[Open RadioInterface]-------------------------
    
    with RadioInterface(args.radioport) as test_obj.ri:
        
        #------------------------------[Get test info]------------------------------

        gui=mcvqoe.gui.TestInfoGui()
        
        gui.chk_audio_function=lambda : mcvqoe.hardware.single_play(
                                                    test_obj.ri,test_obj.audio_interface,
                                                    )
        
        #if recovering, re-use notes and things
        if(recover):
            gui.info_in['test_type'] =test_obj.info['test_type']
            gui.info_in['tx_dev'] = test_obj.info['tx_dev']
            gui.info_in['rx_dev'] = test_obj.info['rx_dev']
            gui.info_in['system'] = test_obj.info['system']
            gui.info_in['test_loc'] = test_obj.info['test_loc']
            gui.info_in['Pre Test Notes']=test_obj.info['Pre Test Notes'] + \
                                          'Test restarted due to error\n'+ \
                                          f'Data loaded from : {args.data_file}\n'
                                          #TODO : add restarted trial number?
        
        test_obj.info=gui.show()

        #check if the user canceled
        if(test_obj.info is None):
            print(f"\n\tExited by user")
            sys.exit(1)
        

        #------------------------------[Run Test]------------------------------
        test_obj.run(recovery=recover)
    
if __name__ == "__main__":
    
    main()