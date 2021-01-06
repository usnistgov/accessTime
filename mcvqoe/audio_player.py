import math
import os
import queue
import scipy.io.wavfile
import scipy.signal
import sys
import threading

from fractions import Fraction

import numpy as np
import sounddevice as sd
import soundfile as sf

def cb_stereo_rec(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""

    if status:
        print(status, file=sys.stderr, flush=True)
    q_rec.put(indata.copy())

def cb_mono_play_rec(indata, outdata, frames, time, status):
    """
    Callback function for the stream.
    Will run as long as there is audio data to play.
    Currently setup to play mono audio files.
    
    """
    
    # Record the output
    qr.put_nowait(indata.copy())
    
    if status.output_underflow:
        print('Output underflow: increase blocksize?', file=sys.stderr)
        raise sd.CallbackStop
    assert not status
    try:
        data = q.get_nowait()
    except queue.Empty:
        print('Buffer is empty: increase buffersize?', file=sys.stderr)
        raise sd.CallbackStop
    if data.size < outdata.size:
        outdata[:len(data),0] = data
        outdata[len(data):] = 0
        raise sd.CallbackStop
    else:
        # One column for mono output
        outdata[:,0] = data
    
class AudioPlayer:
    
    def __init__(self, fs=int(48e3), blocksize=512, buffersize=20, overplay=1.0,input_chans=1,output_chans=1,start_signal=False):
        
        self.sample_rate = fs
        self.blocksize = blocksize
        self.buffersize = buffersize
        self.overplay = overplay
        self.device = AudioPlayer.find_device()
        self.input_chans=input_chans
        self.output_chans=output_chans
        self.start_signal=start_signal
    
    #TODO allow different device defaults
    @staticmethod
    def find_device():
    
        devs = sd.query_devices()
        
        for d in devs:
            if(d['max_input_channels']>0 and d['max_output_channels']>0 and  'UMC' in d['name']):
                return d['name']
           
    def record_stereo(self, filename):
        """
        Record a stereo file and save to 'filename'. Used for 2loc Rx.
        
        ...
        
        Parameters
        ----------
        filename : str
            The file extension to write audio to.

        """
        
        sd.default.device = self.device
        
        global q_rec
        q_rec = queue.Queue()
        
        try:

            # Make sure the file is opened before recording anything:
            with sf.SoundFile(filename, mode='x', samplerate=self.sample_rate,
                              channels=2) as file:
                with sd.InputStream(samplerate=self.sample_rate, device=sd.default.device,
                                    channels=2, callback=cb_stereo_rec):
                    
                    print('#' * 80, flush=True)
                    print('Recording started, please press Ctrl+C to stop the recording', flush=True)
                    print('#' * 80, flush=True)
                    while True:
                        file.write(q_rec.get())
                        
        except KeyboardInterrupt:
            print('\nRecording finished')
        except Exception as e:
            sys.exit(type(e).__name__ + ': ' + str(e))
    
    def play_record(self, audio, filename="rec.wav"):
        """
        Play 'audio' and record to 'filename'. Plays self.input_chans channels
        and records self.output_chans. if self.start_singal is True then the
        last output channel is used for the start signal.
        
        ...
        
        Parameters
        ----------
        audio : numpy array
            The audio in numpy array format. Needs to be in proper sample rate.
        filename : str
            The file extension to write audio data to and return str.
        """
        #TODO: make this actually work, just call play_rec_mono for now
        self.play_rec_mono(audio, filename)
    
    def play_rec_mono(self, audio, filename="rec.wav"):
        """
        Play 'audio' and record to 'filename'. Used for 2loc Tx and 1loc.
        
        ...
        
        Parameters
        ----------
        audio : numpy array
            The audio in numpy array format. Needs to be in proper sample rate.
        filename : str
            The file extension to write audio data to and return str.
        """
        
        # Set device and number of I/O channels
        sd.default.device = self.device
        sd.default.channels = [1, 1]
        
        fs = self.sample_rate

        # Queue for recording input
        global qr
        qr = queue.Queue()
        # Queue for output WAVE file
        global q
        q = queue.Queue(maxsize=self.buffersize)
        
        # Thread for callback function
        event = threading.Event()
        
        # NumPy audio array placeholder
        arr_place = 0
        
        # Add Overplay
        if (self.overplay != 0):
            overplay = fs * self.overplay
        audio = np.pad(audio, (0, int(overplay)), mode='constant')

        for x in range(self.buffersize):
            
            data_slice = audio[self.blocksize*x:(self.blocksize*x)+self.blocksize]
            
            if data_slice.size == 0:
                break
            
            # Save place of NumPy array slice for next loop
            arr_place += self.blocksize
            
            # Pre-fill queue
            q.put_nowait(data_slice)  
        
        # Output and input stream in one
        # Latency of zero to try and cut down delay    
        stream = sd.Stream(   
            blocksize=self.blocksize, samplerate=fs,
            dtype='float32', callback=cb_mono_play_rec, finished_callback=event.set,
            latency=0)
        
        with sf.SoundFile(filename, mode='x', samplerate=fs,
                          channels=1) as rec_file:
            with stream:
                timeout = self.blocksize * self.buffersize / fs

                # For grabbing next blocksize slice of the NumPy audio array
                itrr = 0
                
                while data_slice.size != 0:
                    
                    data_slice = audio[arr_place+(self.blocksize*itrr):arr_place+(self.blocksize*itrr)+self.blocksize]
                    itrr += 1
                    
                    q.put(data_slice, timeout=timeout)
                    rec_file.write(qr.get())
                # Wait until playback is finished
                event.wait()  
                
            # Make sure to write any audio data still left in the recording queue
            while (qr.empty() != True):
                rec_file.write(qr.get())
        
        return filename