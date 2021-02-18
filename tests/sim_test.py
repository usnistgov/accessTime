#!/usr/bin/env python

import mcvqoe.simulation
import unittest
import tempfile
import pkgutil
import scipy.io.wavfile
import scipy.signal
import numpy as np
from fractions import Fraction
import math
import io
import os
import mcvqoe

class AudioTest(unittest.TestCase):
    
    def assertTol(self, value,expected, tol):
        """Fail if value is equal within tolerance"""
        self.assertGreaterEqual(value, expected-tol*expected,f'expected value {expected}')
        self.assertLessEqual(value, expected+tol*expected,f'expected value {expected}')
    
    def test_basic(self):
        
        fs_dev=int(48e3)
        
        audio_file=io.BytesIO(pkgutil.get_data('mcvqoe','audio_clips/test.wav'))
        fs_file, audio_dat= scipy.io.wavfile.read(audio_file)
        
        # Calculate resample factors
        rs_factor = Fraction(fs_dev/fs_file)
        # Convert to float sound array
        audio_dat = mcvqoe.audio_float(audio_dat)
        # Resample audio
        audio = scipy.signal.resample_poly(audio_dat, rs_factor.numerator, rs_factor.denominator)
   
        with mcvqoe.simulation.QoEsim(fs=fs_dev) as sim_obj,\
            tempfile.TemporaryDirectory() as tmp_dir:
            ap=sim_obj
            ri=sim_obj
            #generate the name for the file
            test_name=os.path.join(tmp_dir,'test.wav')
            #request access to channel
            ri.ptt(True)
            #play audio
            ap.play_record(audio, test_name)
            #release channel
            ri.ptt(False)
            
            self.assertTrue(os.path.exists(test_name))
    
    def test_m2e(self):
        
        fs_dev=int(48e3)
        
        min_corr=0.76
        
        audio_file=io.BytesIO(pkgutil.get_data('mcvqoe','audio_clips/test.wav'))
        fs_file, audio_dat= scipy.io.wavfile.read(audio_file)
        
        # Calculate resample factors
        rs_factor = Fraction(fs_dev/fs_file)
        # Convert to float sound array
        audio_dat = mcvqoe.audio_float(audio_dat)
        # Resample audio
        audio = scipy.signal.resample_poly(audio_dat, rs_factor.numerator, rs_factor.denominator)
   
        with mcvqoe.simulation.QoEsim(fs=fs_dev) as sim_obj,\
            tempfile.TemporaryDirectory() as tmp_dir:
            ap=sim_obj
            ri=sim_obj
            
            for m2e in (0.022,0.1,0.3,0.5):
                with self.subTest(mouth2ear=m2e):                
                    sim_obj.m2e_latency=m2e
                    #generate the name for the file
                    test_name=os.path.join(tmp_dir,'test.wav')
                    #request access to channel
                    ri.ptt(True)
                    #play audio
                    ap.play_record(audio, test_name)
                    #release channel
                    ri.ptt(False)
                    
                    self.assertTrue(os.path.exists(test_name))
                    
                    fs_file, rec_dat= scipy.io.wavfile.read(test_name)
                    
                    dly_res = mcvqoe.ITS_delay_est(audio, rec_dat, "f", fsamp=fs_file,min_corr=min_corr)
                    
                    #check if we got a value
                    self.assertFalse(not np.any(dly_res))
                    
                    estimated_m2e_latency=dly_res[1] / fs_file
                    
                    #check that we are within 1%
                    self.assertTol(estimated_m2e_latency,m2e,0.01)
    
    def test_PTT_signal(self):
        
        fs_dev=int(48e3)
        
        audio_file=io.BytesIO(pkgutil.get_data('mcvqoe','audio_clips/test.wav'))
        fs_file, audio_dat= scipy.io.wavfile.read(audio_file)
        
        # Calculate resample factors
        rs_factor = Fraction(fs_dev/fs_file)
        # Convert to float sound array
        audio_dat = mcvqoe.audio_float(audio_dat)
        # Resample audio
        audio = scipy.signal.resample_poly(audio_dat, rs_factor.numerator, rs_factor.denominator)
        
        with mcvqoe.simulation.QoEsim(fs=fs_dev) as sim_obj,\
            tempfile.TemporaryDirectory() as tmp_dir:
            ap=sim_obj
            ri=sim_obj
            #set output channels
            ap.rec_chans={'rx_voice':0,'PTT_signal':1}
            ap.playback_chans={'tx_voice':0,'start_signal':1}
            #generate the name for the file
            test_name=os.path.join(tmp_dir,'test.wav')
            
            for ptt_dly in (0.2,0.5,0.7,1,2,2.5,5):
                with self.subTest(dly=ptt_dly):
            
                    #set up radio interface to expect the start signal
                    ri.ptt_delay(ptt_dly,use_signal=True)
                    #play/record audio
                    ap.play_record(audio,test_name)
                    
                    state=ri.waitState()
                    
                    ri.ptt(False)
                
                    self.assertEqual(state,'Idle')        
                    
                    fs_file, audio_dat= scipy.io.wavfile.read(test_name)
                    
                    
                    # Calculate niquest frequency
                    fn = fs_file/2
                    
                    # Create lowpass filter for PTT signal processing
                    ptt_filt = scipy.signal.firwin(400, 200/fn, pass_zero='lowpass')
                    
                    # Extract push to talk signal (getting envelope)
                    ptt_sig = scipy.signal.filtfilt(ptt_filt, 1, abs(audio_dat[:, 1]))            

                    # Get max value
                    ptt_max = np.amax(ptt_sig)
                    
                    # Normalize levels
                    ptt_sig = ((ptt_sig*math.sqrt(2))/ptt_max)
                    
                    #check levels
                    self.assertFalse(ptt_max < 0.25)
                    
                    # get PTT start index
                    ptt_st_idx = np.nonzero(ptt_sig > 0.5)[0][0]
                    
                    # Convert sample index to time
                    st = ptt_st_idx/fs_file
                    
                    #check if we are within 1%
                    self.assertTol(st,ptt_dly,0.01)
            
        
      
        
    
if __name__ == "__main__":
    unittest.main()
