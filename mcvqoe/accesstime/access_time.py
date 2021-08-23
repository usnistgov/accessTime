import abcmrt
import argparse
import csv
import datetime
import mcvqoe.base
import os
import pkg_resources
import pickle
import scipy.interpolate
import scipy.signal
import time
import timeit

from .version import version
from fractions import Fraction
from mcvqoe.base.terminal_user import terminal_progress_update, terminal_user_check
from mcvqoe.math import approx_permutation_test

import numpy as np


def chans_to_string(chans):
    # channel string
    return '('+(';'.join(chans))+')'


def mk_format(header):

    fmt = ""

    for col in header:
        # split at first space
        col = col.split()[0]
        # remove special chars
        col = ''.join(c for c in col if c.isalnum())
        # need to not use special names
        # TODO : should this be done better?
        if (col == 'try'):
            col = 'rtry'

        fmt += '{'+col+'},'
    # replace trailing ',' with newline
    fmt = fmt[:-1]+'\n'

    return fmt
    

#generate filter for PTT signal
#NOTE : this relies on fs being fixed!!
# Calculate niquest frequency
fn = abcmrt.fs/2
# Create lowpass filter for PTT signal processing
ptt_filt = scipy.signal.firwin(400, 200/fn, pass_zero='lowpass')


class measure:
    """
    Class to run access time measurements.

    The accesstime measure class is used to run access time measurements.
    These can either be measurements with real communications devices or 
    simulated Push-to-talk (PTT) systems.

    Attributes
    ----------
    audio_files : list
        Lis of names of audio files. Relative paths are relative to audio_path.
    audio_path : string
        Path were audio is stored. 
    audio_interface : mcvqoe.AudioPlayer or mcvqoe.simulation.QoEsim
        interface to use to play and record audio on the communication channel
    auto_stop : bool, default=True
        Determines if tests are automatically stopped when the intelligibility
        of P1 is determined to be equivalent to P2.
    bgnoise_file : string
        Name of audio file to use as background noise during measurement.
    bgnoise_volume : float, default=0.1
        volume of background noise.
    data_file : TODO
        TODO : This looks unused, what is it for???
    dev_dly : float
        Mouth-to-ear latency inherent to the measurement system. Determined by
        running a mouth-to-ear latency characterization measurement. This
        delay must be accounted for in access time measurements for accurate
        results.
    get_post_notes : function or None
        Function to call to get notes at the end of the test. Often set to
        mcvqoe.post_test to get notes with a gui popup.
        lambda : mcvqoe.post_test(error_only=True) can be used if notes should
        only be gathered when there is an error
    info : dict
        Dictionary with test info to for the log entry
    inter_word_diff : TODO
        TODO : This thing seems not really used, why do we care? actually, why is it even a class property?
    no_log : tuple of strings
        static property that is a tuple of property names that will not be added
        to the 'Arguments' field in the log. This should not be modified in most
        cases
    outdir : string, default=''
        Base directory where data is stored
    ptt_delay : list
        ptt_delay can be a 1 or 2 element list of floats. If it is a 1 element
        list, then it specifies the minimum PTT delay that will be used with
        the maximum being the end of the first word in the clip. If it is a
        two element list then the first element is the smallest PTT delay used
        and the second is the largest. Defaults to 0 (start of clip).
    ptt_gap : float
        Time to pause, in seconds, between one trial and the next.
    ptt_rep : int
        Number of times to repeat a given PTT delay value. If auto_stop is
        used, ptt_rep must be at least 15.
    ptt_step : float
        Time, in seconds, between successive PTT delays. Default is 20 ms.
    rec_file : string, default=None
        Filename for recovery file. If set to a recovery file, the test will be restarted.
    ri : mcvqoe.RadioInterface or mcvqoe.QoEsim
        Object to use to key the audio channel.
    user_check : function, default=mcvqoe.base.terminal_user.terminal_user_check
        Function that is called to notify the user that they should check the radio
    s_thresh : double, default=-50
        The threshold of A-weight power for P2, in dB, below which a trial is
        considered to have no audio. Defaults to -50.
    s_tries : int, default=3
        Number of times to retry a trial before giving up and ended up the
        measurement. Defaults to 3.
    stop_rep : int, default=10
        Number of times that access must be detected in a row before the test
        is complete. In particular, checks for intelligibility equivalency
        between P1 and P2 at consecutive time steps.
    time_expand : list
        Length of time in seconds of extra audio to send to ABC-MRT16. Adding
        time aids in ABC-MRT16 returning accurate intelligibility estimates.
        A single element list sets time expand before and after the keyword. A
        two element list sets the time at the beginning and the end of the
        keyword respectively.
    pause_trials : int, default=100
        Number of trials to run at a time. Test will run the number of trials
        before pausing for user input. This allows for battery changes or
        radio cooling if needed. If pausing is not desired set pause_trials to
        np.inf.
    progress_update : function, default=mcvqoe.base.terminal_user.terminal_progress_update
        function to call to provide updates on test progress. This function
        takes three positional arguments, prog_type, total number of trials, current
        trial number. Depending on prog_type, different information is displayed to the user.
    split_audio_dest : str, default=None
        Location to store split audio. Intended for (yet to be completed)
        reprocess.

    Methods
    -------

    run()
        run a measurement with the properties of the instance.
    param_check()
        TODO
    load_dat()
        TODO

    Examples
    --------
    Example of running a test with simulated devices

    >>> import mcvqoe.simulation
    >>> import numpy as np
    >>> sim_obj = mcvqoe.simulation.QoEsim(
                    playback_chans = {'tx_voice':0, 'start_signal':1},
                    rec_chans = {'rx_voice':0, 'PTT_signal':1},
                    )

    >>> test_obj = mcvqoe.accesstime.measure(ri=sim_obj,
                                             audio_interface=sim_obj,
                                             pause_trials = np.Inf)
    >>> test_obj.run()
    """
    data_header = ['PTT_time', 'PTT_start', 'ptt_st_dly', 'P1_Int', 'P2_Int',
                   'm2e_latency', 'channels', 'TimeStart', 'TimeEnd',
                   'TimeGap']

    bad_header = ['FileName', 'trial_count', 'clip_count', 'try#', 
                  'p2A-weight', 'm2e_latency', 'channels', 'TimeStart', 
                  'TimeEnd', 'TimeGap']
    
    def __init__(self, **kwargs):

        self.audio_files = [
            pkg_resources.resource_filename(
                "mcvqoe.accesstime", "audio_clips/F1_b9_w1_bed.wav"
                ),
            pkg_resources.resource_filename(
                "mcvqoe.accesstime", "audio_clips/F3_b31_w2_law.wav"
                ),
            pkg_resources.resource_filename(
                "mcvqoe.accesstime", "audio_clips/M3_b38_w1_hang.wav"
                ),
            pkg_resources.resource_filename(
                "mcvqoe.accesstime", "audio_clips/M4_b14_w1_not.wav"
                )
            ]
        self.audio_path = ""
        self.audio_interface = None
        self.auto_stop = True
        self.bgnoise_file = ""
        self.bgnoise_volume = 0.1
        self.data_file = ""
        self.dev_dly = float(31e-3)
        self.get_post_notes = None
        self.info = {'Test Type': 'default', 'Pre Test Notes': ''}
        self.inter_word_diff = 0.0 # Used to compare inter word delays
        self.no_log = ('test', 'ri')
        self.outdir = ""
        self.ptt_delay = [0.0]
        self.ptt_gap = 3.1
        self.ptt_rep = 30
        self.ptt_step = float(20e-3)
        self.rec_file = None
        self.ri = None
        self.user_check = terminal_user_check
        self.s_thresh = -50
        self.s_tries = 3
        self.stop_rep = 10
        self.time_expand = [100e-3 - 0.11e-3, 0.11e-3]
        self.pause_trials = 100
        self.progress_update = terminal_progress_update
        self.split_audio_dest = None
        self.save_tx_audio = True
        self.save_audio = True

        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise TypeError(f"{k} is not a valid keyword argument")

    def load_audio(self):
        """
        load audio files for use in test.
        
        this loads audio from self.audio_files and stores values in self.y,
        self.cutpoints. In most cases run() will call this automatically but,
        it can be called in the case that self.audio_files is changed after
        run() is called.

        Parameters
        ----------

        Returns
        -------

        Raises
        ------
        ValueError
            If self.audio_files is empty
        RuntimeError
            If clip fs is not 48 kHz
        """
   
        #if we are not using all files, check that audio files is not empty
        if not self.audio_files:
            #TODO : is this the right error to use here??
            raise ValueError('Expected self.audio_files to not be empty')

        #check if we are making split audio
        if(self.split_audio_dest):
            #make sure that splid audio directory exists
            os.makedirs(self.split_audio_dest,exist_ok=True)

        #list for input speech
        self.y=[]
        #list for cutpoints
        self.cutpoints=[]
        #list for word spacing
        self.inter_word_diff=0.0
        
        # If noise file was given, laod and resample to match audio files
        if (self.bgnoise_file):
            nfs, nf = mcvqoe.base.audio_read(self.bgnoise_file)
            rs = Fraction(abcmrt.fs/nfs)
            nf = mcvqoe.base.audio_float(nf)
            nf = scipy.signal.resample_poly(nf, rs.numerator, rs.denominator)
        
        for f in self.audio_files:
            #make full path from relative paths
            f_full=os.path.join(self.audio_path,f)
            # load audio
            fs_file, audio_dat = mcvqoe.base.audio_read(f_full)
            #check fs
            if(fs_file != abcmrt.fs):
                raise RuntimeError(f'Expected fs to be {abcmrt.fs} but got {fs_file} for {f}')
                
            #add noise if given
            if self.bgnoise_file:
                if (nf.size != audio_dat.size):
                    #resize to fit
                    n_nf=np.resize(nf, audio_dat.size)
                    #add to array
                    audio_dat = audio_dat + n_nf*self.bgnoise_volume
            # Convert to float sound array and add to list
            self.y.append( audio_dat )
            #strip extension from file
            fne,_=os.path.splitext(f_full)
            #add .csv extension
            fcsv=fne+'.csv'
            #load cutpoints
            cp=mcvqoe.base.load_cp(fcsv)
            
            #check cutpoints
            words = len(cp)
            if (words != 4):
                raise ValueError(f"Loading {cutpoint}: 4 'words' expected but, {words} found")
            
            if not np.isnan(cp[0]['Clip']) or not np.isnan(cp[2]['Clip']):
                raise ValueError(f"Loading {fcsv}: Words 1 and 3 must be silence")
            
            if (cp[1]['Clip'] != cp[3]['Clip']):
                raise ValueError(f"Loading {fcsv}: Words 2 and 4 must be the same")
            
            # Check inter word delays
            inter_delay = (cp[2]['End'] - cp[2]['Start']) / self.audio_interface.sample_rate
            if (self.inter_word_diff == 0.0):
                self.inter_word_diff = inter_delay
            else:
                if (self.inter_word_diff != inter_delay):
                    #give warning
                    self.progress_update(
                                'warning',
                                0,0,
                                msg='It is recommended that all inter word times are the same',
                            )
            
            #add cutpoints to array
            self.cutpoints.append(cp)

    def set_time_expand(self,t_ex):
        """
        convert time expand from seconds to samples and ensure a 2 element vector.
        
        This is called automatically in run and post_process and, normally, it
        is not required to call set_time_expand manually

        Parameters
        ----------
        t_ex :
            time expand values in seconds
        Returns
        -------
        """
        self._time_expand_samples=np.array(t_ex)
        
        if(len(self._time_expand_samples)==1):
            #make symmetric interval
            self._time_expand_samples=np.array([self._time_expand_samples,]*2)

        #convert to samples
        self._time_expand_samples=np.ceil(
                self._time_expand_samples*abcmrt.fs
                ).astype(int)

    def run(self, recovery=False):
        """Run an Access Time test
        
        ...
        
        Parameters
        ----------
        recovery : Boolean
            Is this a recovery from a previous test?
        
        """
        
        #----------------[List of Vars to Save in Pickle File]----------------
        
        save_vars = ( 'clip_names', 'bad_name', 'temp_data_filenames',
                      'ptt_st_dly', 'wavdir' , 'ptt_step_counts' )
        
        # Initialize clip end time for gap time calculation
        time_e = np.nan
        tg_e = np.nan
        
        #-----------------------[Check audio sample rate]-----------------------
        
        if (self.audio_interface.sample_rate != abcmrt.fs):
            raise ValueError(f'audio_interface sample rate is {self.audio_interface.sample_rate} Hz but only {abcmrt.fs} Hz is supported')
        
        #------------------[Check for correct audio channels]------------------
        
        if('tx_voice' not in self.audio_interface.playback_chans.keys()):
            raise ValueError('self.audio_interface must be set up to play tx_voice')
        if('start_signal' not in self.audio_interface.playback_chans.keys()):
            raise ValueError('self.audio_interface must be set up to play start_signal')
            
        if('rx_voice' not in self.audio_interface.rec_chans.keys()):
            raise ValueError('self.audio_interface must be set up to record rx_voice')
        if('PTT_signal' not in self.audio_interface.rec_chans.keys()):
            raise ValueError('self.audio_interface must be set up to record PTT_signal')
            
        #---------------------------[Set time expand]---------------------------
        self.set_time_expand(self.time_expand)
                   
        #---------------------[Generate csv format strings]---------------------
        
        dat_format = mk_format(self.data_header)
        bad_format = mk_format(self.bad_header)
        
        #------------------[Load In Old Data File If Given]-------------------
        
        if recovery:

            trial_count = 0

            #compare versions
            if('version' not in self.rec_file):
                #no version, so it must be old, give warning
                self.progress_update('warning',0,0,
                                        msg='recovery file missing version')
            elif version != self.rec_file['version']:
                #warn on version mismatch, recovery could have issues
                self.progress_update('warning',0,0,
                                        msg='recovery file version mismatch!')

            # Restore saved class properties
            for k in self.rec_file:
                if k.startswith('self.') and not k == 'self.rec_file':
                    varname=k[len('self.'):]
                    self.__dict__[varname]=self.rec_file[k]

            # Copy recovery variables to current test
            ptt_st_dly = self.rec_file['ptt_st_dly']
            ptt_step_counts = self.rec_file['ptt_step_counts']

        # Only read in data if this is the first time
        else:

            # Set initial loop indices
            clip_start = 0
            k_start = 0
            kk_start = 0

            self.load_audio()

        #-------------------------[Get Test Start Time]-------------------------

        self.info['Tstart'] = datetime.datetime.now()
        dtn = self.info['Tstart'].strftime('%d-%b-%Y_%H-%M-%S')
        
        #--------------------------[Fill log entries]--------------------------
        
        #set test name
        self.info['test'] = 'Access'
        #add abcmrt version
        self.info['abcmrt version'] = abcmrt.version
        #fill in standard stuff
        self.info.update(mcvqoe.base.write_log.fill_log(self))

        #-----------------[Initialize Folders and Filenames]------------------

        #generate data dir names
        data_dir     = os.path.join(self.outdir,'data')
        wav_data_dir = os.path.join(data_dir,'wav')
        csv_data_dir = os.path.join(data_dir,'csv')
        rec_data_dir = os.path.join(data_dir, 'recovery')
        
        
        #create data directories 
        os.makedirs(csv_data_dir, exist_ok=True)
        os.makedirs(wav_data_dir, exist_ok=True)
        os.makedirs(rec_data_dir, exist_ok=True)
        
        #generate base file name to use for all files
        base_filename='capture_%s_%s'%(self.info['Test Type'],dtn);
        
        #generate test dir names
        wavdir=os.path.join(wav_data_dir,base_filename) 
        
        #create test dir
        os.makedirs(wavdir, exist_ok=True)
        
        #get name of audio clip without path or extension
        clip_names=[ os.path.basename(os.path.splitext(a)[0]) for a in self.audio_files]
        
        # Generate csv filenames and add path
        self.data_filenames = []
        temp_data_filenames = []
        for name in clip_names:
            file = f"{base_filename}_{name}.csv"
            tmp_f = f"{base_filename}_{name}_TEMP.csv"
            file = os.path.join(csv_data_dir, file)
            tmp_f = os.path.join(csv_data_dir, tmp_f)
            self.data_filenames.append(file)
            temp_data_filenames.append(tmp_f)

        # Generate filename for bad csv data
        bad_name = f"{base_filename}_BAD.csv"
        bad_name = os.path.join(csv_data_dir, bad_name)

        #-----------------------[Do more recovery things]-----------------------

        if recovery:
            # Boolean array to see which files to copy to new name
            copy_files = np.full(len(temp_data_filenames), False)
            # Save old names to copy to new names
            old_filenames = self.rec_file['temp_data_filenames']
            # Save old .wav folder
            old_wavdir = self.rec_file['wavdir']
            # Save old bad file name
            old_bad_name = self.rec_file['bad_name']

            for k in range(len(temp_data_filenames)):
                save_dat = self.load_dat(old_filenames[k])
                if not save_dat:
                    self.progress_update(
                                'status',
                                len(temp_data_filenames),
                                k,
                                f"No data file found for {old_filenames[k]}"
                            )
                else:
                    self.progress_update(
                                'status',
                                len(temp_data_filenames),
                                k,
                                f"initializing with data from {old_filenames[k]}"
                            )
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
                        k_start = k_start

                    # Assign kk_start point for inner loop
                    if (clen == 0):
                        kk_start = 0
                    else:
                        kk_start = ((clen-1) % self.ptt_rep)

        #---------[Write Transmit Audio File(s) and cutpoint File(s)]----------

        #write out Tx clips and cutpoints to files
        #cutpoints are always written, they are needed for eval
        for dat,name,cp in zip(self.y,clip_names,self.cutpoints):
            out_name=os.path.join(wavdir,f'Tx_{name}')
            #check if saving audio, cutpoints are needed for processing
            if(self.save_tx_audio and self.save_audio):
                mcvqoe.base.audio_write(out_name+'.wav', int(self.audio_interface.sample_rate), dat)
            mcvqoe.base.write_cp(out_name+'.csv',cp)

        #-----------------------[Generate PTT Delays]-------------------------
        
        if not recovery:
        
            ptt_st_dly = []
            ptt_step_counts = []
    
            if (len(self.ptt_delay) == 1):
                for num in range(len(self.cutpoints)):
                    # Word start time from end of first silence
                    w_st = (self.cutpoints[num][0]['End']/self.audio_interface.sample_rate)
                    # Word end time from end of word
                    w_end = (self.cutpoints[num][1]['End']/self.audio_interface.sample_rate)
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
                    ptt_step_counts.append(len(ptt_st_dly[-1]))
            else:
                for _ in range(len(self.cutpoints)):
                    dly_steps = np.arange(self.ptt_delay[1], self.ptt_delay[0], -self.ptt_step)
                    ptt_st_dly.append(dly_steps)
                    ptt_step_counts.append(len(dly_steps))
    
            # Running count of the number of completed trials
            trial_count = 0

        #----------------[Pickle important data for restart]------------------
        
        # Initialize error file
        recovery_file = os.path.join(rec_data_dir,base_filename+'.pickle')
         
        # Error dictionary, add version
        err_dict = {'version' : version}
         
        for var in save_vars:
            err_dict[var] = locals()[var]
         
        # Add all access_time object parameters to error dictionary
        for i in self.__dict__:
            skip = ['no_log', 'audio_interface', 'ri',
                    'inter_word_diff', 'get_post_notes',
                    'progress_update', 'user_check']
            if (i not in skip):
                err_dict['self.'+i] = self.__dict__[i]
         
        # Place dictionary into pickle file
        with open(recovery_file, 'wb') as pkl:
            pickle.dump(err_dict, pkl)
        
        #---------------------------[write log entry]---------------------------
        
        mcvqoe.base.pre(info=self.info, outdir=self.outdir)

        #-----------------------[Notify User of Start]------------------------
        
        # Turn on LED
        self.ri.led(1, True)
    
        try:
    
            #---------------------[Save Time for Set Timing]----------------------
            
            set_start = datetime.datetime.now().replace(microsecond=0)
    
            #----------------------------[Clip Loop]------------------------------
            
            #load templates outside the loop so we take the hit here
            abcmrt.load_templates()
            
            for clip in range(clip_start, len(self.y)):
                
                #---------------------[Calculate Delay Start Index]-------------------
                
                # Calculate index to start M2E latency at. This is 3/4 through the second silence.
                # If more of the clip is used, ITS_delay can get confused and return bad values.
                dly_st_idx = (int(self.cutpoints[clip][2]['Start'] + 0.75*(self.cutpoints[clip][2]['End']
                                                                      -self.cutpoints[clip][2]['Start'])))
                
                
                #---------------------[Update Total Trials]---------------------
                
                total_trials = sum(ptt_step_counts)*self.ptt_rep                
                
                # Check if file is not present (not a restart)
                if (True):
                    
                    #-------------------------[Write CSV Header]--------------------------
                    
                    with open(temp_data_filenames[clip], 'w', newline='') as csv_file:
                        writer = csv.writer(csv_file)
                        writer.writerow([f'Audiofile = {self.audio_files[clip]}'])
                        writer.writerow([f'fs = {self.audio_interface.sample_rate}'])
                        writer.writerow(['----------------'])
                        writer.writerow(self.data_header)
                    
                    #Update with name and location of datafile    
                    if (not self.progress_update(
                                'csv-update',
                                total_trials,
                                trial_count,
                                clip_name=clip_names[clip],
                                file=temp_data_filenames[clip]
                            )):
                        raise SystemExit()
                        
                    #-----------------------------[Stop Flag]-----------------------------
                    
                    success = np.zeros((2, (len(ptt_st_dly[clip])*self.ptt_rep)))

                    # Stop flag is computed every delay step
                    stop_flag = np.empty(len(ptt_st_dly[clip]))
                    stop_flag[:] = np.nan
                    
                    # Initialize clip count
                    clip_count = 0

                #-----------------------[Delay Step Loop]-----------------------
                
                for k in range(k_start, len(ptt_st_dly[clip])):

                    #-------------[Update Current Clip and Delay]---------------

                    if(not self.progress_update(
                                'acc-clip-update',
                                total_trials,
                                trial_count,
                                clip_name=clip_names[clip],
                                delay=ptt_st_dly[clip][k],
                            )):
                        raise SystemExit()
                    
                    #-------------------------[Measurement Loop]--------------------------
                    
                    for kk in range(kk_start, self.ptt_rep):
                        
                        #---------------[Update User Progress]-----------------

                        if(not self.progress_update(
                                    'test',
                                    total_trials,
                                    trial_count,
                                )):
                            raise SystemExit()
                        #-----------------------[Increment Trial Count]-----------------------
                        
                        trial_count = trial_count + 1
                        
                        #------------------------[Increment Clip Count]-----------------------
                        
                        clip_count = clip_count + 1
                        
                        

                        
                        #-----------------------------[Check Loop]----------------------------
                        
                        # flag for loop
                        low_p2_aw=True
                        
                        # Number of retries for this clip
                        retries = 0
                        
                        while low_p2_aw:
                            
                            retries = retries + 1
                            
                            # Check if we've exceded retry limit
                            if (retries > self.s_tries):
                                
                                # Turn on LED when waiting for user input
                                self.ri.led(2, True)
                                # TODO Check if we have retry function
                                user_exit = self.user_check(
                                        'problem-stop',
                                        "Audio not detected through the system."
                                    )
                                
                                # Turn off LED, resuming
                                self.ri.led(2, False)
                                
                                if(user_exit):
                                    raise SystemExit()
                                
                            #---------------------[Key Radio and Play Audio]----------------------

                            # Setup the push to talk to trigger
                            self.ri.ptt_delay(ptt_st_dly[clip][k], use_signal=True)
                            
                            # Save end time of previous clip
                            time_last = time_e
                            tg_last = tg_e
                            
                            # Create audiofile name/path for recording
                            audioname = f"Rx{clip_count}_{clip_names[clip]}.wav"
                            audioname = os.path.join(wavdir, audioname)
                            
                            # Get start timestamp
                            time_s = datetime.datetime.now().replace(microsecond=0)
                            tg_s = timeit.default_timer()
                            
                            # Play and record audio data
                            rec_names = self.audio_interface.play_record(self.y[clip], audioname)
                            
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
                                if(not self.progress_update(
                                            'warning',
                                            total_trials,
                                            trial_count,
                                            msg='PTT Delay longer than clip',
                                        )):
                                    raise SystemExit()
                            else:
                                # Unknown state
                                raise RuntimeError(f"Unknown radio interface wait state: {state}")

                            #------------------------[Pause Between Runs]-------------------------
                            
                            time.sleep(self.ptt_gap)
                            
                            #-------------------------[Data Processing]---------------------------
                            
                            data = self.process_audio(clip,audioname,rec_names,dly_st_idx)
                            
                            #TODO : intelligibility for autostop
                            success[0, clip_count-1] = data['P1Int']
                            success[1, clip_count-1] = data['P2Int']
                            
                            data['pttstdly'] = ptt_st_dly[clip][k]
                            
                            #----------------------[Add times to data]---------------------
                            
                            # Calculate gap time (try/except here for nan exception)
                            try:
                                time_gap = tg_s - tg_last
                            except:
                                time_gap = np.nan
                                
                            # Format time_gap for CSV file
                            if np.isnan(time_gap):
                                data['TimeGap'] = 'nan'
                            else:
                                data['TimeGap'] = f"{(time_gap//3600):.0f}:{((time_gap//60)%60):.0f}:{(time_gap%60):.3f}"
                
                            data['TimeStart'] = time_s.strftime('%H:%M:%S'),
                            data['TimeEnd'] = time_e.strftime('%H:%M:%S'),
                            
                            #----------------------[Check A-weight of P2]---------------------
                                                     
                            low_p2_aw = data['p2Aweight'] <= self.s_thresh
                                                     
                            if low_p2_aw:
                                if(not self.progress_update(
                                        'check-fail',
                                        total_trials,
                                        trial_count,
                                        msg=f'A-weight power for P2 is {data["p2Aweight"]:.2f}dB',
                                    )):
                                    raise SystemExit()
                                
                                # Save bad audiofile
                                wav_name = f"Bad{clip_count}_r{retries}_{clip_names[clip]}"
                                wav_name = os.path.join(wavdir, wav_name)
                                #rename file to save it and record again
                                os.rename(audioname, wav_name)
                                
                                self.progress_update(
                                        'status',
                                        total_trials,
                                        trial_count,
                                        msg=f"Saving bad data to '{bad_name}'"
                                    )
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
                                            **data,
                                        )
                                    )
                                    
                        #--------------------------[End Check Loop]---------------------------
                        
                        #----------------------[Inform User of Restart]-----------------------
                        
                        # Check if it took more than one try
                        if (retries > 1):
                            if (not self.progress_update(
                                        'check-resume',
                                        total_trials,
                                        trial_count,
                                        msg=f'A-weight power of {data["p2Aweight"]:.2f} dB for P2',
                                    )):
                                raise SystemExit()
                            
                        #-------------------------[Save Trial Data]---------------------------
                        
                        with open(temp_data_filenames[clip], 'a') as csv_file:
                            csv_file.write(
                                dat_format.format(
                                    **data,
                                )
                            )
                        
                        #------------------------[Check Trial Limit]--------------------------
                        
                        if ((trial_count % self.pause_trials) == 0):
                            
                            # Calculate set time
                            time_diff = datetime.datetime.now().replace(microsecond=0)
                            set_time = time_diff - set_start
                            
                            # Turn on LED when waiting for user input
                            self.ri.led(2, True)
                            
                            # wait for user
                            user_exit = self.user_check(
                                    'normal-stop',
                                    'check batteries.',
                                    trials=self.pause_trials,
                                    time=set_time,
                                )
                            
                            # Turn off LED, resuming
                            self.ri.led(2, False)
                                
                            if(user_exit):
                                raise SystemExit()
                            
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
                    if (self.auto_stop and (self.cutpoints[clip][1]['End']/self.audio_interface.sample_rate)>ptt_st_dly[clip][k]):
                        if (self.stop_rep<=k and all(stop_flag[(k-self.stop_rep):k])):
                            #stopped early, update step counts
                            ptt_step_counts[clip] = k
                            # If stopping condition met, break from loop
                            break

                #-----------------------[End Delay Step Loop]-------------------------
                
                # Reset start index so we start at the beginning
                k_start = 0
            
            #--------------------------[End Clip Loop]----------------------------
            
            #--------------------[Change Name of Data Files]----------------------
            
            for k in range(len(temp_data_filenames)):
                #give user update on csv rename
                #return value not checked, test is finished so no abort possible
                self.progress_update(
                                'csv-rename',
                                len(temp_data_filenames),
                                k,
                                file=temp_data_filenames[k],
                                new_file=self.data_filenames[k],
                            )
                os.rename(temp_data_filenames[k], self.data_filenames[k])
                
            #----------------------[Delete recovery file]----------------------
            
            os.remove(recovery_file)

        finally:
            if (self.get_post_notes):
                #get notes
                info = self.get_post_notes()
            else:
                info = {}
            #finish log entry
            mcvqoe.base.post(outdir=self.outdir, info=info)

    def process_audio(self,clip_index,fname,rec_chans,dly_st_idx):
    
        #-----------------------[Load in recorded audio]-----------------------
 
        # Get latest run Rx audio
        dat_fs, rec_dat = mcvqoe.base.audio_read(fname)
        
        #get index of rx_voice channel
        voice_idx = rec_chans.index('rx_voice')
        #get voice channel
        voice_dat=rec_dat[:,voice_idx]
        
        #get index of PTT_signal
        psig_idx = rec_chans.index('PTT_signal')
        #get PTT signal data
        psig_dat=rec_dat[:,psig_idx]
        
        #----------------------------[Calculate M2E]----------------------------
        
        # Calculate delay. Only use data after dly_st_idx
        (_,dly) = mcvqoe.delay.ITS_delay_est(
            self.y[clip_index][dly_st_idx:], 
            voice_dat[dly_st_idx:],
            mode='f',
            dlyBounds=[0, np.inf],
            fs=self.audio_interface.sample_rate
        )
        
        #convert to seconds
        estimated_m2e_latency = dly/self.audio_interface.sample_rate
        
        #---------------------[Compute intelligibility]---------------------
        
        #strip filename for basename in case of split clips
        if(isinstance(self.split_audio_dest, str)):
            (bname,_)=os.path.splitext(os.path.basename(fname))
        else:
            bname=None
        
        data=self.compute_intelligibility(
                                          voice_dat,
                                          self.cutpoints[clip_index],
                                          dly,clip_base=bname
                                          )
                
        
        #--------------------------[Compute ptt_time]--------------------------
        
        data['PTTstart'] = self.process_ptt(psig_dat)
        
        # Get ptt time. Subtract nominal play/record delay
        # (can be seen in PTT Gate data)
        data['PTTtime']= data['PTTstart'] - self.dev_dly
        
        #----------------------------[Add M2E data]----------------------------

        data['m2elatency'] = estimated_m2e_latency
        
        #----------------------------[Add channels]----------------------------

        data['channels'] = chans_to_string(rec_chans)
        
        return data
        
    def compute_intelligibility(self,audio,cutpoints,cp_shift,clip_base=None):
        
        #array of audio data for each word
        word_audio=[]
        #array of word numbers
        word_num=[]
        #maximum index in audio array
        max_idx=len(audio)-1
        
        for cp_num,cpw in enumerate(cutpoints):
            if(not np.isnan(cpw['Clip'])):
                #calculate start and end points
                start=np.clip(cp_shift+cpw['Start']-self._time_expand_samples[0],0,max_idx)
                end  =np.clip(cp_shift+cpw['End']  +self._time_expand_samples[1],0,max_idx)
                #add word audio to array
                word_audio.append(audio[start:end])
                #add word num to array
                word_num.append(cpw['Clip'])                
                
                if(clip_base and isinstance(self.split_audio_dest, str)):
                    outname=os.path.join(self.split_audio_dest,f'{clip_base}_cp{cp_num}_w{cpw["Clip"]}.wav')
                    #write out audio
                    mcvqoe.base.audio_write(outname, int(abcmrt.fs), audio[start:end])
                
        _, success = abcmrt.process(word_audio, word_num)

        #put data into return array
        data={
              'P1Int' : success[0],
              'P2Int' : success[1],
             }
    
        #compute a weight power of word two here, because we have the cut audio
        data['p2Aweight'] = mcvqoe.base.a_weighted_power(word_audio[1],self.audio_interface.sample_rate)
        
        return data
        
    def process_ptt(self,signal):
        '''
        Compute PTT time from ptt signal.
        
        Parameters
        ----------
        signal : numpy vector
            Audio recording vector of the PTT signal.
        
        Returns
        -------
        float
            The time, in seconds from the start of the clip, that the PTT was
            pushed at.
        '''
        
        # Extract push to talk signal (getting envelope)
        ptt_sig = scipy.signal.filtfilt(
                            ptt_filt,
                            1,
                            np.absolute(signal)
                        )

        # Get max value
        ptt_max = np.amax(ptt_sig)
        
        # Check levels
        if(ptt_max < 0.25):
            if(not self.progress_update(
                        'warning',
                        total_trials,
                        trial_count,
                        msg='Low PTT signal values. Check levels',
                    )):
                raise SystemExit()

            
        # Normalize levels
        ptt_sig = ((ptt_sig*np.sqrt(2))/ptt_max)
        
        try:
            # Determine turn on sample
            ptt_st_idx = np.nonzero(ptt_sig > 0.5)[0][0]
            
            # Convert sample index to time
            st = ptt_st_idx/self.audio_interface.sample_rate
            
        except IndexError:
            st = np.nan
        
        # Return when the ptt was pushed    
        return st
            
    def param_check(self):
        """Check all input parameters for value errors"""
        
        if ((self.auto_stop) and (self.ptt_rep < 16)):
            raise ValueError(f"ptt_rep must be greater than 15 if autostop is used.")
        
        # Time expand check and resize if necessary
        if (len(self.time_expand) < 1):
            raise ValueError(f"Time expand must be more at least one value")
        if (len(self.time_expand) > 2):
            raise ValueError(f"Time expand can only be a maximum of two values")
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
        
        try:
            # Read csv file and occupy list, skipping header section
            with open(fname) as csv_f:
                #burn the first 4 lines in the file
                for n in range(4):
                    csv_f.readline()
                #dict reader to get data
                reader = csv.DictReader(csv_f, fieldnames=self.data_header)
                for row in reader:
                    dat_list.append(row)

                return dat_list
        except FileNotFoundError:
            return None
