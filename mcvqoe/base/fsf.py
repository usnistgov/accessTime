import math
import mcvqoe.delay
import warnings

import numpy as np

from scipy import signal
from scipy.fft import fft

def fsf(tx_data, rx_data, fs=48E3):
    """
    Purpose
    -------
    Frequency slope fit distortion detector using Uniform Bands.
    
    Parameters
    ----------
    tx_data : numpy array
        Transmit audio data.
    rx_data : numpy array
        Received audio data.
    fs : double, optional
        Sample rate. The default is 48E3.
  
    Returns
    -------
    score : double
        FSF score.
    dly_samples : tuple or int
        M2E latency.

    """
    
    _, delay_samples = mcvqoe.delay.ITS_delay_est(rx_data, tx_data, mode='f', fs=48000)
    dly_samples = delay_samples
    if delay_samples < 0:
        #raise ValueError('Negative delay detected.')
        warnings.warn('Negative delay detected. Setting delay to zero.')
        delay_samples = 0
        
    if len(rx_data) < (len(tx_data) + delay_samples):
        rx_data = rx_data[delay_samples:]
    else:
        rx_data = rx_data[delay_samples:(len(tx_data) + delay_samples)]
    
    tx_slope = calc_slope(tx_data)
    
    rx_slope = calc_slope(rx_data)
        
    score = np.true_divide(rx_slope, tx_slope)
    
    return score, dly_samples
    
def calc_slope(wav_data):
    """
    Purpose
    -------
    Calculates frequency slope fit for a 
    given audio clip.
    
    Parameters
    ----------
    wav_data : numpy array
        Audio data.
    band_x : bool
        Determines whether or not linear fit x values
        come from band centers (false) or band numbers
        (true).

    Returns
    -------
    slope : double
        Slope of wav_data.

    """
    
    freq_set = np.array([[200, 450], 
                [400, 650], 
                [600, 850], 
                [800, 1050], 
                [1000, 1250],
                [1200, 1450],
                [1400, 1650], 
                [1600, 1850],
                [1800, 2050],
                [2000, 2250],
                [2200, 2450],
                [2400, 2650],
                [2600, 2850],
                [2800, 3050], 
                [3000, 3250]])
    
    fft_len = 2 ** 14
    
    num_bands = len(freq_set)

    #TODO: Check if already a column vector (avoid transpose if so)
    if wav_data.shape != (len(wav_data), ):
        wav_data = wav_data.T
    
    #TODO: Explore length of hamming window - see if length of window should be less than length of input wav data 
    # It seems that using the window in "signal.periodogram" is better than getting it here
    win = signal.get_window('hamming', len(wav_data))
  
    wav_win = win * wav_data
    
    # Perform periodogram function (equivalent to GNU Octave's built in periodogram)
    pxx, freq = periodogram(x=wav_data, window=win, nfft=fft_len, fs=int(48e3))
    
    band_vals = np.zeros((num_bands))
    
    for band in range(num_bands):
        mask = np.logical_and((freq >= freq_set[band, 0]), (freq <= freq_set[band, 1]))
        band_vals[band] = 10 * math.log10(np.mean(pxx[mask]))
  
    # Get index of max value, only consider the first half of FI bands
    max_idx = np.argmax(band_vals[0:(num_bands//2)])
    
    # Range of fit to the right of max
    fit_range = np.arange(max_idx, band_vals.shape[0])

    # x-axis values from band number
    x_vals = np.arange(0, num_bands)
    # Eliminate unused bands
    x_vals = x_vals[fit_range]

    # Using np.p.p.polyfit as is suggested in documentation
    p = np.polynomial.polynomial.polyfit(x_vals, band_vals[fit_range], 1)

    intercept = p[0]
    slope = p[1]

    return slope

def periodogram(x, window, nfft, fs):
    """
    Purpose
    -------
    Periodogram implementation that mimics Octave's implementation (periodogram_simple).

    Parameters
    ----------
    x : numpy array 
        Input signal.
    window : numpy array
        Window. It must be the same length as the input signal.
    nfft : int
        Number of DFT points.
    fs : int
        Sample rate. It must be positive.

    Returns
    -------
    None.

    """

    n = len(x)
    x = np.multiply(x, window)
    
    if n > nfft:
        rr = n % nfft
        
        if rr != 0:
            x = np.concatenate((x, np.zeros(nfft-rr)), axis=None)

        # Reshape uses 'order="F"' to match MATLAB version of reshape
        x = np.sum(np.reshape(x, (nfft, -1), order="F"), axis=1)
        
    n = np.sum(np.square(window))

    pxx = np.true_divide(np.square(np.abs(fft(x, n=nfft, axis=0))), n)
    pxx = np.true_divide(pxx, fs)
    
    # nfft is even
    if nfft % 2 == 0:
        psd_len = (nfft // 2) + 1
        tmp_arr = pxx[nfft-1: psd_len-1: -1]
        tmp_arr = np.append(tmp_arr, 0)
        tmp_arr = np.insert(tmp_arr, 0, 0)
        pxx = np.add(pxx[: psd_len], tmp_arr)

    # nfft is odd
    else:
        psd_len = (nfft + 1) // 2
        tmp_arr = pxx[nfft-1: psd_len-1: -1]
        tmp_arr = np.insert(tmp_arr, 0, 0)
        pxx = np.add(pxx[: psd_len], tmp_arr)
    
    freq = np.true_divide(np.arange(0, (nfft // 2)+1), nfft)
    freq = freq * fs

    return pxx, freq