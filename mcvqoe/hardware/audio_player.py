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

class AudioPlayer:
    
    def __init__(self, fs=int(48e3), blocksize=512, buffersize=20, overplay=1.0,rec_chans=1,playback_chans=1,start_signal=False):
        
        self.sample_rate = fs
        self.blocksize = blocksize
        self.buffersize = buffersize
        self.overplay = overplay
        self.device = AudioPlayer.find_device()
        self.rec_chans=rec_chans
        self.playback_chans=playback_chans
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


    
    def play_record(self, audio, filename):
        """
        Play 'audio' and record to 'filename'.
        
        Plays self.playback_chans channels and records self.rec_chans. if 
        self.start_singal is True then the last output channel is used for the
        start signal.
        Parameters
        ----------
        audio : numpy array
            The audio in numpy array format. Needs to be in proper sample rate.
        filename : str
            The file extension to write audio data to and return str.
        """
         # Set device and number of I/O channels
        sd.default.device = self.device
        sd.default.channels = [self.rec_chans, self.playback_chans]
        
        # Add start signal to audio channel 2
        if (self.start_signal):
            # Signal frequency
            f_sig = 1e3
            # Signal time
            t_sig = 22e-3
            # Calculate time for playback
            t = np.arange(float(len(audio)))
            t = t/self.sample_rate
            # Calculate clip start signal
            t = np.where((t < t_sig), np.sin(2*np.pi*1000*t), 0)
            # Add column to mono audio file (channel 2)
            audio = audio[..., np.newaxis]
            audio = np.pad(audio, ((0, 0), (0, 1)), mode='constant')
            # Add start signal to audio
            audio[:, 1] = t
        
        # Add Overplay
        if (self.overplay != 0):
            audio = np.pad(audio,
                                (0, int(self.sample_rate * self.overplay)),
                                mode='constant')
            
        #check for 1D audio
        if(len(audio.shape)==1):
            #promote a 1D array to a 2D nx1 array
            audio.shape=(audio.shape[0],1)

        # Queue for recording input
        self._qr = queue.Queue()
        # Queue for playback output
        self._qpb = queue.Queue(maxsize=self.buffersize)
        
        # Thread for callback function
        event = threading.Event()
        
        # NumPy audio array placeholder
        arr_place = 0
            
        for x in range(self.buffersize):
            
            data_slice = audio[self.blocksize*x:(self.blocksize*x)+self.blocksize]
            
            if data_slice.size == 0:
                break
            
            # Save place of NumPy array slice for next loop
            arr_place += self.blocksize
            
            # Pre-fill queue
            self._qpb.put_nowait(data_slice)  
        
        # Output and input stream in one
        # Latency of zero to try and cut down delay    
        stream = sd.Stream(   
            blocksize=self.blocksize, samplerate=self.sample_rate,
            dtype='float32', callback=self._cb_play_rec, finished_callback=event.set,
            latency=0)
        
        with sf.SoundFile(filename, mode='x', samplerate=self.sample_rate,
                          channels=self.rec_chans) as rec_file:
            with stream:
                timeout = self.blocksize * self.buffersize / self.sample_rate

                # For grabbing next blocksize slice of the NumPy audio array
                itrr = 0
                
                while data_slice.size != 0:
                    
                    data_slice = audio[arr_place+(self.blocksize*itrr):arr_place+(self.blocksize*itrr)+self.blocksize]
                    itrr += 1
                    
                    self._qpb.put(data_slice, timeout=timeout)
                    rec_file.write(np.squeeze(self._qr.get()))
                # Wait until playback is finished
                event.wait()  
                
            # Make sure to write any audio data still left in the recording queue
            while (self._qr.empty() != True):
                rec_file.write(np.squeeze(self._qr.get()))

        
    def _cb_play_rec(self,indata, outdata, frames, time, status):
        """
        Callback function for the stream.
        Will run as long as there is audio data to play.
        Currently setup to play stereo.
        
        """

        # Record the output
        self._qr.put_nowait(indata.copy())
        
        if status.output_underflow:
            print('Output underflow: increase blocksize?', file=sys.stderr)
            raise sd.CallbackStop
        assert not status
        try:
            data = self._qpb.get_nowait()
        except queue.Empty:
            print('Buffer is empty: increase buffersize?', file=sys.stderr)
            raise sd.CallbackStop
        if data.size < outdata.size:
            outdata[:len(data)] = data
            outdata[len(data):] = 0
            raise sd.CallbackStop
        else:
            outdata[:] = data
