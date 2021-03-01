
from mcvqoe import audio_float

import numpy as np
import datetime

soft_time_fmt='TM%j-%Y_%H-%M-%S.%f'

def softTimeDecode(audio):
    if(len(audio.shape) != 1):
        raise ValueError('Input must be a numpy vector')
    times=[]
    
    #Get prefix from time format
    prefix=soft_time_fmt[:soft_time_fmt.index('%')]
    
    #TODO : raise error if prefix is zero length???
    
    #convert to integer values
    audio=np.round(audio_float(audio)*255.0).astype(int)
    
    #convert sequence to numpy array
    npPre=np.array([ord(c) for c in prefix])
    
    #indicies for sliding window
    winIdx=np.arange(audio.size-len(prefix)+1)[:,None]+np.arange(len(prefix))
    
    #find where the window matches
    tc_idx=(audio[winIdx] == npPre).all(1).nonzero()[0]
    
    for idx in tc_idx:
        #get the index of the end of the timecode
        end_idx=idx+min(np.where(audio[idx:]==0)[0])
        #get time string
        tc_str=''.join([chr(c) for c in audio[idx:end_idx]])
        time=datetime.datetime.strptime(tc_str,soft_time_fmt)
        #append time and index to array
        times.append((idx,time))
        
    return times