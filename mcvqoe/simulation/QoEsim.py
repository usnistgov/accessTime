
import os.path
import scipy.io.wavfile as wav
import numpy as np
import tempfile
import shutil
import scipy.signal
import subprocess
from mcvqoe.misc import audio_float

class QoEsim:
    def __init__(self,port=None,debug=False):
        
        self.debug=debug
        self.PTT_state=[False,]*2
        self.LED_state=[False,]*2
        self.ptt_wait_delay=[-1.0,]*2
        self.chanel_tech='clean'
        self.pre_impairment=None
        self.post_impairment=None
        self.channel_impairment=None
        self.dvsi_path='pcnrtas'
        #TODO : determine good delays for analog and amr
        self.standard_delay={'clean' : 0,'p25': 348/8e3,'analog' : 0,'amr':0}
        #try to find ffmpeg in the path
        self.fmpeg_path=shutil.which('ffmpeg')
        #TODO : set based on tech
        self.m2e_latency=21.1e-3
        self.fs=48e3
        self.access_delay=0
        #TODO : just made this up, should probably have a sane default
        self.noise_level=0.1e-3
    
    def __enter__(self):
        
        return self
    
    def ptt(self,state,num=1):
        ''' 
            PTT - change the push-to-talk status of the radio interface

            PTT(state) if state is true then the PTT is set to transmit. if state is
        False then the radio is set to not transmit

        PTT(state,num) same as above but control the ptt of radio number num
        instead of radio number 1
        '''
            
        self.PTT_state[num]=bool(state)
        #clear wait delay
        self.ptt_wait_delay[num]=-1
            
    def led(self,num,state):
        '''turn on or off LED's on the radio interface board

        LED(num,state) changes the state of the LED given by num. If state is
        true turn the LED on if state is False turn the LED off'''

        #determine LED state string
        if(state):
            if(self.debug):
                print("RadioInterface LED {%num} state is on")
        else:
            if(self.debug):
                print("RadioInterface LED {%num} state is off")
        
        self.LED_state[num]=bool(state)
        
        
    def devtype(self):
        '''get the devicetype string from the radio interface

        dt = DEVTYPE() where dt is the devicetype string'''

        #TODO : simulate other versions??
        return 'MCV radio interface v1.0'


    def pttState(self):
        ''' returns the pttState for a radioInterface object. This is called
        automatically when pttState is accessed'''

        return self.PTT_state
            



    def waitState(self):
        '''returns the WaitState for a radioInterface object. this is called
        automatically when WaitState is accessed'''

        #TODO: do we need to simulate this better?
        return 'Idle'

    def ptt_delay(self,delay,num=1,use_signal=False):
        '''setup the radio interface to key the radio after a delay

        PTT_DELAY(dly) set the radio to be keyed in dly seconds.

        PTT_DELAY(dly,use_signal=True) set the radio to be keyed dly seconds
        after the start signal is detected.

        PTT_DELAY(dly,num=n,__) same as above but used key radio number n
        instead of radio number one

        delay=PTT_DELAY(dly,__) same as above but return the actual delay set on
        the microcontroller. This is different because of rounding and limits on
        the possible delay
        '''

        self.ptt_wait_delay[num]=delay
        #set state to true, this isn't 100% correct but the delay will be used 
        #for the sim so, it shouldn't matter
        self.PTT_state[num]=True
        
        
    def temp(self):
        '''read value from temperature sensors

           [ext,int]=temp() - returns the temperature measured by the thermistor
           external to the radiointerface or the temperature sensor built into the
           MSP430
        '''
        
        #TODO : generate better fake values??
        return (38,1500)


    #delete method
    def __del__(self):
        #nothing to do here
        pass
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        
        self.ptt(False)
        self.led(1, False)
        
    # =====================[audio channel simulation function]=====================
    def simulate_audio_channel(self,tx_data):
        
        #add pre channel impairments
        if(self.pre_impairment):
            tx_dat=self.pre_impairment(tx_data,self.fs)
    
        # for a clean vocoder, write the rx signal as is
        if self.chanel_tech == "clean":
            
            if(self.channel_impairment):
                warnings.warn('There is no channel for the \'clean\' option. can not use channel_impairment')
            
            rx_data = tx_data
        
        elif self.chanel_tech == "analog":
            # do later
            pass
        
        elif self.chanel_tech == "p25":
            channel_data = self.p25encode(tx_data, self.fs)
            
            #apply channel impairments
            if(self.channel_impairment):
                channel_data=self.channel_impairment(channel_data)
            
            rx_data = self.p25decode(channel_data, self.fs)
        
        # simulate passing the signal thru an LTE vocoder by using ffmpeg
        elif self.chanel_tech == "lte":
        
            with tempfile.TemporaryDirectory() as temp_dir:
                # create paths for temporary wav and amr outputs
                temp_wav = os.path.join(temp_dir, "temp_out.wav")
                temp_amr = os.path.join(temp_dir, "temp_out.amr")
                
                # write the rx signal as a wav so it can be converted to amr
                wav.write(temp_wav, int(self.fs), rx_data)
                # use ffmpeg to convert rx wav file to rx wav file
                # explantion of flags:
                # -hide_banner (supresses excessive terminal output)
                # -loglevel warning (supresses excessive terminal output)
                # -channel_layout mono (specifies that the signal is mono)
                # -i %s (defines input file as temp_wav)
                # -ar 16k (changes the sample rate to 16k as required for amr conversion)
                # -b:a 23.85k (changes the bit rate to 23.85k - highest bit rate
                #              allowed for amr conversion)
                # -codec amr_wb (specifies conversion to amr wide band)
                # -y %s (specified output file as temp_amr)
                subprocess.run(
                    [self.fmpeg_path,'-hide_banner','-loglevel','error',
                        '-channel_layout','mono','-i',temp_wav,'-ar','16k',
                        '-b:a','23.85k','-codec','amr_wb','-y',temp_amr]
                )
                
                #apply channel impairments
                if(self.channel_impairment):
                    #TODOD : load channel data
                    channel_data=self.channel_impairment(channel_data)
                    #TODOD : write channel data
                    
                
                # convert temp amr file back to wav, and resample to original sample rate
                subprocess.run(
                    [self.fmpeg_path,'-hide_banner','-loglevel','error',
                        '-channel_layout','mono','-codec','amr_wb','-i',temp_amr,
                        '-ar',str(int(self.fs)),'-y',rx_file]
                )
                # read data from new rx wav file
                _, rx_data = wav.read(rx_file)
        else:
            raise ValueError(f'"{self.chanel_tech}" is not a valid technology')
        
        
        #add post channel impairments
        if(self.post_impairment):
            rx_dat=self.post_impairment(rx_data,self.fs)
    
        return rx_data

    # =====================[record audio function]=====================
    def play_record(self,audio, buffersize=20, blocksize=512,out_name='', overPlay=1):


        #generate gaussian noise, and add it to audio (simulates low level noise in real life transmit audio)
        noise = np.random.normal(0, self.noise_level, len(audio)).astype(np.float32)

        audio = audio + noise 
        
        try:
            #get offset for channel technology
            m2e_offset=self.standard_delay[self.chanel_tech]
        except KeyError:
            #a key error means we used a bad technology
            raise ValueError(f'"{self.chanel_tech}" is not a valid technology')
            
        #calculate values in samples
        overplay_samples=int(overPlay*self.fs)
        #correct for audio channel latency
        m2e_latency_samples=int((self.m2e_latency-m2e_offset)*self.fs)
        
        if(m2e_latency_samples<0):
            #TODO : it might be possible to get around this but, it sounds slightly nontrivial...
            raise ValueError(f'Unable to simulate a latency of {self.m2e_latency}. Minimum simulated latency for technology \'{self.chanel_tech}\' is {m2e_offset}')
        
        #check if PTT was keyed during audio
        if(self.ptt_wait_delay[1] == -1):
            #PTT wait not set, don't simulate access time
            ptt_st_dly_samples=0
            access_delay_samples=0
        else:
            ptt_st_dly_samples=int(self.ptt_wait_delay[1]*self.fs)
            access_delay_samples=int(self.access_delay*self.fs)
        
        #append overplay to audio   
        overplay_audio = np.zeros(int(overplay_samples), dtype=np.float32)
        tx_data_with_overplay = np.concatenate((audio, overplay_audio))
        
        #mute portion of tx_data that occurs prior to triggering of PTT
        muted_samples = int(access_delay_samples + ptt_st_dly_samples)
        muted_tx_data_with_overplay = tx_data_with_overplay[muted_samples:]
        
        #generate raw rx_data from audio channel
        rx_data = self.simulate_audio_channel(muted_tx_data_with_overplay)
        
        #generate silent noise section comprised of ptt_st_dly, access delay and m2e latency audio snippets
        silence_length = int(ptt_st_dly_samples + access_delay_samples + m2e_latency_samples)
        
        #derive mean and standard deviation from real-world noise observed in the audio recordings
        mean = 0
        std = 1.81e-5
        
        silent_section = np.random.normal(mean, std, silence_length)
        
        #prepend silent section to rx_data
        rx_data = np.concatenate((silent_section, rx_data))
        
        #force rx_data to be the same length as tx_data_with_overplay
        rx_data = rx_data[:np.size(tx_data_with_overplay)]
           
        #write out audio file
        wav.write(out_name, int(self.fs), rx_data)
        
    # =====================[p25 encode function]=====================
    def p25encode(self,x, rate):
        # given a signal x with fs: rate, returns encoded p25

        # resample signal to 8000 Hz, and scale by 2^15
        new_len = int(len(x) * 8000 / rate)
        x = scipy.signal.resample(x, new_len)
        x = (x * (2 ** 15)).astype(np.int16)

        with tempfile.TemporaryDirectory() as temp_dir:
            # create paths for audio and encoded files
            audio_name = os.path.join(temp_dir, "audio")
            enc_name = os.path.join(temp_dir, "encoding.bin")

            # write audio file
            x.tofile(audio_name)

            # encode to enc_name
            subprocess.run([self.dvsi_path,'-enc','-fr',audio_name,enc_name],stdout=subprocess.DEVNULL)

            # read p25 encoding
            y = np.fromfile(enc_name, np.uint8)

        # convert p25 encoding to logical values
        y = y.astype(np.bool_)
        return y


    # =====================[p25 decode function]=====================


    def p25decode(self,x, target_rate):
        # assumes x is a signal with fs: 8000
        # deocde signal to target_rate

        with tempfile.TemporaryDirectory() as temp_dir:
            enc_name = os.path.join(temp_dir, "encoding.bin")
            audio_name = os.path.join(temp_dir, "audio")
            # values are either 0 or 255 convert accordingly
            x = (255 * x).astype(np.uint8)
            # write out temporary audio file
            x.tofile(enc_name)

            # decode to audio_name
            subprocess.run([self.dvsi_path,'-dec','-fr',enc_name,audio_name],stdout=subprocess.DEVNULL)

            # read decodede signal
            dat = np.fromfile(audio_name, np.int16)
        # normalize signal to -1 to 1
        dat = audio_float(dat)
        # resample to target_rate
        dat = scipy.signal.resample(dat, int(len(dat) * target_rate / 8000))
        return dat
