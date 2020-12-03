import numpy as np

#convert audio data to float type with standard scale        
def audio_float(dat):
    if(dat.dtype is np.dtype('uint8')):
        return (dat.astype('float')-128)/128
    if(dat.dtype is np.dtype('int16')):
        return dat.astype('float')/(2**15)
    if(dat.dtype is np.dtype('int32')):
        return dat.astype('float')/(2**31)
    if(dat.dtype is np.dtype('float32')):
        return dat 
    if(dat.dtype is np.dtype('float64')):
        return dat    
    else:
        raise RuntimeError(f'unknown audio type \'{dat.dtype}\'')