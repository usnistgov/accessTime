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
    """
    Class to play and record audio for test purposes.
    
    This class has functions for playing and recording audio and is used in QoE
    testing.
        
    Parameters
    ----------
    fs : int
        Sample rate of audio in/out in samples per second.
    blocksize : int
        The size of the blocks that are sent/received to/from the audio device.
    buffersize : int
        The number of blocks in the output buffer.
    overplay : float
        The number of seconds of extra audio to play/record at the end of a clip.
    rec_chans : dict
        Dictionary describing the recording. Dictionary keys should be one of
        {'rx_voice','PTT_signal','timecode','tx_beep'}. The value for each entry
        is the, zero based, channel number that should be recorded for each signal.
    playback_chans : dict
        Dictionary describing the playback channels. Dictionary keys must be one 
        of {'tx_voice','start_signal'}. The value for each entry is the, zero
        based, channel number that each signal should be played on.
    
    Attributes
    ----------
    sample_rate : int
        Sample rate of audio in/out in samples per second.
    blocksize : int
        The size of the blocks that are sent/received to/from the audio device.
    buffersize : int
        The number of blocks in the output buffer.
    overplay : float
        The number of seconds of extra audio to play/record at the end of a clip.
    device : str
        Audio device to use. can be found with find_device().
    rec_chans : dict
        Dictionary describing the recording. Dictionary keys should be one of
        {'rx_voice','PTT_signal','timecode','tx_beep'}. The value for each entry
        is the, zero based, channel number that should be recorded for each signal.
    playback_chans : dict
        Dictionary describing the playback channels. Dictionary keys must be one 
        of {'tx_voice','start_signal'}. The value for each entry is the, zero
        based, channel number that each signal should be played on.
        
    See Also
    --------
    mcvqoe.simulation.QoEsim : Simulated replacement for AudioPlayer.
    
    Examples
    --------
    
    play 48 kHz audio stored in tx_voice and record in a file named 'test.wav'.
    >>>import mcvqoe.hardware.AudioPlayer
    >>>ap=mcvqoe.hardware.AudioPlayer(fs=int(48e3))
    >>>ap.play_record(tx_voice,'test.wav')
    now do the same but also output the start signal on channel 1 and record the
    PTT signal on channel 1.
    >>>ap.playback_chans={'tx_voice':0,'start_signal':1}
    >>>ap.rec_chans={'rx_voice':0,'PTT_signal':1}
    >>>ap.play_record(tx_voice,'test.wav')
    """
    def __init__(self, fs=int(48e3), blocksize=512, buffersize=20, overplay=1.0,rec_chans={'rx_voice':0},playback_chans={'tx_voice':0}):
        
        self.sample_rate = fs
        self.blocksize = blocksize
        self.buffersize = buffersize
        self.overplay = overplay
        self.device = AudioPlayer.find_device()
        self.rec_chans=rec_chans
        self.playback_chans=playback_chans
    
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


    def _get_recording_map(self):
        """
        Get map and names for recording channels.
        
        Returns
        -------
        list of ints
            A channel map of the channel numbers used for each recording channel.
        list of strings
            A list of the names of the channels in the order they will be in in
            the recording file.
        """
        chan_map=[]
        chan_names=[]
        for k,v in self.rec_chans.items():
            chan_map.append(v)
            chan_names.append(k)
        return (chan_map,chan_names)    
        
    
    def play_record(self, tx_voice, filename):
        """
        Play audio out the specified channels and record to 'filename'.
        
        Plays the audio specified by self.playback_chans on the respective
        channels. Records on the channels specified by self.rec_chans. 
       
        Parameters
        ----------
        tx_voice : numpy array
            Voice audio to play through system. Needs to be in proper sample rate.
        filename : str
            The file extension to write audio data to.

        Returns
        -------
        list of strings
            A list of the recorded output channels in the order that they appear
            in the output file.
        
        See Also
        --------
        mcvqoe.simulation.QoEsim : Simulated replacement play_record.
        
        Examples
        --------
        
        play 48 kHz audio stored in tx_voice and record in a file named
        'test.wav'.
        >>>import mcvqoe.hardware.AudioPlayer
        >>>ap=mcvqoe.hardware.AudioPlayer(fs=int(48e3))
        >>>ap.play_record(tx_voice,'test.wav')
        now do the same but also output the start signal on channel 1 and record
        the PTT signal on channel 1.
        >>>ap.playback_chans={'tx_voice':0,'start_signal':1}
        >>>ap.rec_chans={'rx_voice':0,'PTT_signal':1}
        >>>ap.play_record(tx_voice,'test.wav')
        """
        
        if(len(tx_voice.shape)==2):
            if(tx_voice.shape[1]!=1):
                #TODO : warn about dropping channels
                pass
            #only take one channel of input
            tx_voice=tx_voice[:,0]
        
        audio=np.empty((tx_voice.shape[0],len(self.playback_chans)))
        
        #get the highest numbered playback channel
        #this will be the number of channels that will be played
        #account for zero based indexing
        pb_chan=max(self.playback_chans.values())+1
        rec_chan=max(self.rec_chans.values())+1
        
        self._playback_map=[]
        self._playback_silent=set(range(pb_chan))
        
        for n,(k,v) in enumerate(self.playback_chans.items()):
            #add to playback map
            self._playback_map.append(v)
            #remove from silent map
            self._playback_silent.remove(v)
            # Add start signal to audio
            if (k=='start_signal'):
                # Signal frequency
                f_sig = 1e3
                # Signal time
                t_sig = 22e-3
                # Calculate time for playback
                t = np.arange(float(len(audio)))/self.sample_rate
                # Calculate clip start signal
                sig = np.where((t < t_sig), np.sin(2*np.pi*1000*t), 0)
                # Add start signal to audio
                audio[:, n] = sig
            elif(k=='tx_voice'):
                audio[:,n]=tx_voice
            else:
                raise ValueError(f'Unknown output channel : {k}')

        #convert to tuple for calback usage
        self._playback_silent=tuple(self._playback_silent)

        (rec_map,rec_names)=self._get_recording_map()
        
         # Set device and number of I/O channels
        sd.default.device = self.device
        sd.default.channels = [rec_chan,pb_chan]
                
        #check for 1D audio
        if(len(audio.shape)==1):
            #promote a 1D array to a 2D nx1 array
            audio.shape=(audio.shape[0],1)
        
        # Add Overplay
        if (self.overplay != 0):
            audio = np.pad(audio,
                                ((0, int(self.sample_rate * self.overplay)),(0,0)),
                                mode='constant')

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
                          channels=len(self.rec_chans)) as rec_file:
            with stream:
                timeout = self.blocksize * self.buffersize / self.sample_rate

                # For grabbing next blocksize slice of the NumPy audio array
                itrr = 0
                
                while data_slice.size != 0:
                    
                    data_slice = audio[arr_place+(self.blocksize*itrr):arr_place+(self.blocksize*itrr)+self.blocksize]
                    itrr += 1
                    
                    self._qpb.put(data_slice, timeout=timeout)
                    
                    rx_dat=self._qr.get()
                    rec_file.write(rx_dat[:,rec_map])
                # Wait until playback is finished
                event.wait()  
                
            # Make sure to write any audio data still left in the recording queue
            while (self._qr.empty() != True):
                rx_dat=self._qr.get()
                rec_file.write(rx_dat[:,rec_map])
    
        #return the channels in the order recorded in the file
        return rec_names
        
    def _cb_play_rec(self,indata, outdata, frames, time, status):
        """
        Callback function for the stream.
        Will run as long as there is audio data to play.
        
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
        
        if data.shape[0] < outdata.shape[0]:
            outdata[:data.shape[0],self._playback_map] = data
            outdata[:data.shape[0],self._playback_silent] = 0
            outdata[data.shape[0]:,:] = 0
            raise sd.CallbackStop
        else:
            outdata[:,self._playback_map] = data
            outdata[:,self._playback_silent] = 0
