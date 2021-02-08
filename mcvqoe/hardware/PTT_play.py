

import scipy.io.wavfile
import scipy.signal
import sounddevice as sd
from fractions import Fraction
from mcvqoe import audio_float
import tempfile
import pkgutil
import io
import os
import time



def single_play(ri,ap,audio_file=None,playback=False,ptt_wait=0.68):
    """
    Play an audio clip through a PTT system once.
    
    This function plays audio using the given RadioInterface and AudioPlayer
    objects. The output can, optionally, be played back to the usser when
    complete
    
    Parameters
    ----------
    ri : RadioInterface
        Interface to talk to radio PTT.
    ap : AudioPlayer
        Audio player to play audio with.
    audio_file : str, default=None
        Audio file to use for test. if None, use default audio.
    playback : bool, default=False
        If true, play the audio after the trial is complete.
    ptt_wait : float, default=0.68
        Amount of time to wait, in seconds, between PTT and playback.
    """
    
    if(audio_file is None):
        audio_file = io.BytesIO(pkgutil.get_data(__name__,'audio_clips/test.wav'))
    
    #get fs from audio player
    fs=ap.sample_rate
    
    # Gather audio data in numpy array and audio samplerate
    fs_file, audio_dat = scipy.io.wavfile.read(audio_file)
    # Calculate resample factors
    rs_factor = Fraction(fs/fs_file)
    # Convert to float sound array
    audio_dat = audio_float(audio_dat)
    # Resample audio
    audio = scipy.signal.resample_poly(audio_dat, rs_factor.numerator, rs_factor.denominator)

    with tempfile.TemporaryDirectory() as tmp_dir:
        
        #set filename of recording
        rec_file=os.path.join(tmp_dir,'test.wav')
        
        #request access to channel
        ri.ptt(True)
        #pause for access
        time.sleep(ptt_wait)
        #play audio
        ap.play_record(audio, rec_file)
        #release channel
        ri.ptt(False)
        
        if(playback):
            #read in file
            fs_rec, rec_dat = scipy.io.wavfile.read(audio_file)
            #check if we have multiple channels
            if(len(rec_dat.shape)>1):
                #drop all but the first channel
                #this will drop the PTT tone if used and not blow eardrums
                rec_dat=rec_dat[:,0]
            #set sample rate
            sd.default.samplerate = fs_rec
            #play audio over the default device
            sd.play(rec_dat)
