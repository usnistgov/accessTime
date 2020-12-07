import numpy as np
import scipy.signal as sig
import scipy.io.wavfile 

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

def svp56_fast(x,fs=8000):
    #This code implements the "Speech Voltmeter" given in CCITT Rec. P.56.
    #It is a fast version of svp56.m which was written from the description in
    #the hard copy doc that came with UGST STL 96.  svp56.m results have been
    #verified against results of the C code from UGST.
    #
    #svp56_fast.m agrees with with svp56.m as follows.  It either agrees
    #exactly (the integer counts in all 16 bits of "a" match exactly at
    #inspection point A) or almost exactly (the integer counts in some of the
    #16 bits of "a" are off by one at inspection point A, and the asl and saf
    #differ in the 4th or 5th decimal place)
    #Note that on a fixed platform svp56_fast.m requires about 8# of the
    #running time that svp56.m requires
    #
    #Usage:  [asl,saf,active]=svp56_fast(x, fs)
    #
    # INPUTS:
    #x is the speech signal, which can be passed as either a list, numpy array, 
    #   or as a file name. If passed as the string path to a wav file, the wav 
    #   file will be read and converted to a signal
    #fs is the sample rate of x, and will default to 8000
    #
    # OUTPUTS:
    #asl is active speech level in dB (relative to the clipping point of a 
    #   16 bit file)
    #saf is the speech activity factor (0 to 1)
    #active has the same length as the speech signal, it has 1's in active 
    #   areas, 0's elsewhere.  "active" is an approximation, and the average
    #   absolute error: mean(abs( saf - sum(active)/n )) is about 0.2# or 0.3#.
    #
    #Written by S. Voran, in mid 1990's

    #if x is a filename, extact data from the wav file
    if isinstance(x, str):
        fs, x = scipy.io.wavfile(x)
    elif not isinstance(x, (list, np.ndarray)):
        raise ValueError("Invalid input for x")

    
    x = np.array(x)
    #only keep first channel in 2-channel audio
    if len(np.shape(x)) != 1:
        x = x[:,0]
    
    #convert the signal to 16 bit integers in range [-32768, +32767]
    r=2**15
    #scale [-1, +1]
    if type(x[0]) == np.float32:
        x = np.asarray(x * r, dtype=np.int16)
    #scale [-2147483648, +2147483647]
    elif type(x[0]) == np.int32:
        x = np.asarray(x / r / 2, dtype=np.int16)
    #data is already in specified format
    elif type(x[0]) == np.int16:
        pass
    #scale [0, 255]
    elif type(x[0]) == np.uint8:
        offset = -((2**8)-1)/2
        scale = (2**8)+1
        x = np.asarray((x+offset)*scale, dtype=np.int16)


    x=x - np.mean(x)  #mean removal is not in P56, but it should be
    
    r=2**15 
    sq=np.sum(x ** 2)
    if sq==0:
        raise ValueError('No signal')
    x=np.abs(x)  #rectify
    n=len(x) 
    g=np.e ** (-1/(fs*.03))

    q=sig.lfilter([(1-g)**2], [1, -2*g, g*g], x)  #smooth

    c=2 ** np.arange(16)
    a=np.zeros(16) 
    hs=round(.2*fs)  #200 ms hang time

    #take log 2, with handling that gives log2(0)=-100 instead of error
    good=np.nonzero(0<q)[0]
    lq=-100*np.ones(len(q)) 
    lq[good]=np.floor(np.log2(q[good]))   #these 3 lines protect against log2(0), defining it to be log2(0)=-100 
    #print(lq.tolist())
    for i in range(16):
        active=( i <= lq)  #compare log2 of env. with integer values 0 to 15
        trans=np.nonzero(np.abs(np.diff(active)))[0] 
        for j in range(len(trans)):
            active[trans[j]:(min(trans[j]+hs-1,n)+1)]=1  #extend activity 200 ms
            #after each transition
        a[i]=np.sum(active)  #total number of log2(env) samples above a
        #threshold of i-1
    #------------------Inspection point A-----------------------------

    L=(10*np.log10(sq/n))-(20*np.log10(r))  #average power relative to clip point (in dB)
    c=(20*np.log10(c))-(20*np.log10(r))  #binary thresholds relative to clip point (in dB)
    A=np.zeros(len(c)) 
    for i in range(16):
        if a[i]>0:
            A[i]=10*np.log10(sq/a[i])-20*np.log10(r) 
        else:
            A[i]=200
    d=A-c

    Afinal=0
    for i in range(15):
        if d[i]>=15.9 and d[i+1]<=15.9:
            if d[i]-d[i+1]==0:
                Afinal=A[i] 
            else:
                s=(d[i]-15.9)/(d[i]-d[i+1]) 
                Afinal=(1-s)*A[i]+(s*A[i+1])

    saf=10**((L-Afinal)/10) 
    asl=Afinal

    #To get to a target active speech level, you can scale speech based
    #on the output of this code but you might have to iterate a bit to hit
    #an exact value.  This is because the
    #Speech Voltmeter is not exactly linear.  For example, scaling speech by 
    #2.0 does not produce exactly 20*log10(2)=6.02 dB increase in Speech
    #Voltmeter output. But it does typically produce a value in the range
    # 6.02 +/- 0.25 dB.

    #Here ends the code that emulates the ITU-T P.56 Speech Voltmeter.  Below is code to
    #create an activity mask.  It is the intuitive, reasonable extension of the above.
    #Specifically, if sum(a(i)) for some i goes to n, then we have 100# speech activity.
    #This says that the a(i)'s are the speech activities masks.  The a(i)'s are
    #calculated from floor(log2(envelope)).  The floor operation means that non-integral
    #thresholds on this "integer-log-envelope" are not meaningful.  Thus it remains
    #to simply pick the best i value and a(i) is the mask. We recaculate a(i) instead of
    #saving all 16, which could use a lot of memory for long speech files.

    dud=np.min(np.abs(d-15.9))
    loc = np.argmin(np.abs(d-15.9))
    active=( loc <=lq)
    trans=np.nonzero(np.abs(np.diff(active)))[0]
    for j in range(len(trans)):
        active[trans[j]:min(trans[j]+hs-1,n)+1]=1 
    return asl,saf,active
