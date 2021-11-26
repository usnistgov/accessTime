import os
import fnmatch
import mcvqoe.base
import statistics
import argparse
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import plotly.io as pio
pio.renderers.default = 'browser'
import plotly.express as px
import math
import re

def Test_Stats(Wav_Dir):
    """
    Test_Stats Read in a directory of WAV files. 
    Use a-weight, FSF, and clipping checks to inform
    user of potential problems in collected data. Flags
    trials that may require further investigation.
    
    Parameters
    ----------
    Wav_Dir : string
        directory of WAV files

    Returns
    -------
    bad_trial :        

    """
    # Get trial recordings
    print("Loading recordings")
    # Get all the Rx wav files 
    Dir_Files = os.listdir(Wav_Dir)
    Naming = 'Rx*'
    all_wavs = fnmatch.filter(Dir_Files, Naming)
    # Get total number of trials
    Trials = len(all_wavs)
    # Inform user of number of data sets
    print("Number of trials:")
    print(Trials)
    # Create empty list for rx recordings 
    rx_rec = []

    # Cycle through, in order
    for n in range(1,Trials+1):
        start = 'Rx'+str(n)+'_'
        rx_name = [s for s in all_wavs if start in s]
        rx_path = Wav_Dir + '/' + rx_name[0]
        fs,y_rec = mcvqoe.base.audio_read(rx_path)
        rx_rec.append(y_rec[:])   
  
    # Create bad trial set
    bad_trial = {''}
   
    # Find all the Tx files in the wav_dir, strip 
    # the Tx...wav off and then use 
    #if stripped_tx_name in rx_name
    TX_names = 'Tx*'
    TX_obj = fnmatch.filter(Dir_Files, TX_names)
    TX_filename =fnmatch.filter(TX_obj, '*.wav')
    # Create empty list for tx wavs 
    tx_wavs = []
    # Cycle through and get all the TX files
    for k in range(0,len(TX_filename)):
       tx_path = Wav_Dir + '/' + TX_filename[k]
       fs,tx_wavfile = mcvqoe.base.audio_read(tx_path)
       tx_wavs.append(tx_wavfile)
   
def AW_Rec_Check(Trials, rx_rec,fs,all_wavs,bad_trial):
    """
    Calculates the a-weight (dBA) of each trial. Plot these  
    values. Check for trials with a dBA less than - 60 dBA.
    Check for trials with a dBA a certain distance from the mean.
    
    Parameters
    ----------
    Trials : int
        number of trials 
    rx_rec : list 
        audio for rx recordings   
    fs : int 
        sampling rate of rx recordings       
    all_wavs : list
        names of rx recordings   
    bad_trial : set
        names of trials flagged for potential problems

    Returns
    -------
    bad_trial : 
         Aw value and stats, bad_trial, AW bad trials?    
    """
    # Create empty list for a-weight     
    A_Weight = []
    AW_flag = {''}
      
    # Get A-weight
    print("Gathering Statistics and Creating Plots") 
    for k in range(0,Trials): 
        # Calculate the A-weighted power of each recording 
        aw = mcvqoe.base.a_weighted_power(rx_rec[k], fs) 
        A_Weight.append(aw)

    # Plot values 
    A_Weight = np.asarray(A_Weight)  
    dfAW = pd.DataFrame({
      "A-Weight": A_Weight})  
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
        y = dfAW['A-Weight'],
        mode = 'markers'
        )
    )    
    fig.update_layout(title_text='A_Weighted Power of Received Audio')
    fig.update_xaxes(title_text='Trial Number')
    fig.update_yaxes(title_text='A-Weight (dBA)')
    fig.show() 

    # Calculate mean a-weight, standard deviation.
    # Use this info to find trials that may have lost
    # audio. 
    AW_lin = 10**(A_Weight/20)
    AW_low = 10**(-60/20)
    AW_Mean = round(statistics.mean(AW_lin),3)
    AW_std = round(statistics.stdev(AW_lin),3)
    for m in range(0,Trials):
        # Cycle through AW values, look for trials where the values
        # stand out by being a certain distance from the mean
        if abs(AW_lin[m]-AW_Mean) > AW_std:
            # Get the name of the wav file
            AWflag_wav = all_wavs[m]
            # Add it to the bad list
            bad_trial.add(AWflag_wav)
            AW_flag.add(AWflag_wav)
        # Add a flag if the a-weight is below -60 dBA
        if AW_lin[m] < AW_low:
           # Get the name of the wav file
           AWflag_wav = all_wavs[m]
           # Add it to the bad list
           AW_flag.add(AWflag_wav)

def FSF_Rec_Check(TX_filename,tx_wavs,Trials, rx_rec,fs,all_wavs,bad_trial):   
    """
    Calculate FSF scores, standard deviation. Use this info to find trials that may have lost
    audio.
    
    Parameters
    ----------
    TX_filename : list
        names of tx audio files
    tx_wavs   :  list
        audio for tx audio
    Trials : int
        number of trials 
    rx_rec : list 
        audio for rx recordings   
    fs : int 
        sampling rate of rx recordings       
    all_wavs : list
        names of rx recordings   
    bad_trial : set
        names of trials flagged for potential problems

    Returns
    -------
    
    """
    # Create empty list for FSF scores     
    FSF_all = []
    # Get FSF scores, plot trials
    print("Gathering FSF data") 
    # cycle through, match RX names to tx names
    # Get just the names of tx files, remove the Tx and .wav 
    tx_base_name = []
    for n in range(0,len(TX_filename)):
        tx_justname = re.sub('\.wav$', '', TX_filename[n])
        tx_justname = tx_justname[3:]
        tx_base_name.append(tx_justname)   
   # Get just the names of rx files, remove the Rx and .wav 
   rx_base_name = []
   for n in range(0,len(all_wavs)):
       rx_justname = re.sub('\.wav$', '', all_wavs[n])
       rx_justname = rx_justname[3:]
       rx_base_name.append(rx_justname)
    
    # Find RX files with the matching tx name LEFT OFF HERE
    
    
    for j in all_wavs: 
        for m in tx_base_name:
           # Get the associated file for that name wav, both TX and RX 
           if m in j:
               
               #Pull the associated file names and wavs and list them
               indexTest = all_wavs.index(tx_base_name)
               # then i want these to be linked
               dfTxRx= pd.DataFrame({"RX_name":all_wavs, 
                                     "RX_dat":rx_rec[j],
                                     "TX_name":filename,
                                     "TX_dat":tx_wavs[m]})
      
    
    
    # Get FSF scores for each tx-rx pair
    for k in Trials: 
        get_fsf = mcvqoe.base.fsf(rx_rec[k],tx_wavs[0], fs)
        FSF_all.append(get_fsf)   
        
    # Gather metrics for FSF scores
    FSF_Mean = round(statistics.mean(FSF_all),3)
    FSF_std = round(statistics.stdev(FSF_all),3)
    for m in Trials:
        # Cycle through FSF scores, look for trials where the score
        # stands out by being a certain distance from the mean
        if abs(FSF_all[m]-FSF_Mean) > FSF_std:
            # Get the name of the wav file
            FSFflag_wav = all_wavs[m]
            # Add it to the bad list
            bad_trial.add(FSFflag_wav)     


def Clip_Rec_Check(Trials, rx_rec, all_wavs,bad_trial):
    """
    Cycle through all rx recordings and check if any clipped.
    Parameters
    ----------
    Trials : int
        number of trials 
    rx_rec : list 
        audio for rx recordings         
    all_wavs : list
        names of rx recordings   
    bad_trial : set
        names of trials flagged for potential problems

    Returns
    -------
   
    """
    # Set up warning threshold
    vol_high = -1
    # Create empty list for peak volume    
    peak_dbfs = []
    for n in range(0,Trials):
        # check for positive and negative clipping
        peak = max(abs(rx_rec[n]))
        peak_db = round(20 * math.log10(peak), 2)
        peak_dbfs.append(peak_db)
        # If approaching clipping, flag as a bad trial
        if peak_dbfs[n] > vol_high :
            # Get the name of the wav file
            clip_wav = all_wavs[n]
            # Add it to the bad list
            bad_trial.add(clip_wav)
    
    
def Wav_Plot(rx_rec,Trials,fs):
    """
    Plot rx trial audio recordings
    
    Parameters
    ----------
    Trials : int
        number of trials 
    rx_rec : list 
        audio for rx recordings   
    fs : int 
        sampling rate of rx recordings       

    Returns
    -------
 
    """
    # Create empty list for time (seconds)
    tsec = []
    # Prepare time info for plotting
    for k in range(0,Trials):
        t = len(rx_rec[0])/fs
        ts = np.arange(0,t,1/fs)
        tsec.append(ts)
        # Plot recording
        dfTest= pd.DataFrame({"time":ts, 
                        "audio":rx_rec[0]})
    dfTest.set_index('time')
    fig = px.line(dfTest, y='audio',x='time')
    fig.update_layout(title_text='Trial Recordings')
    fig.update_xaxes(title_text='Time (s)')
    fig.update_yaxes(title_text='Amplitude')
    fig.show()    

# Handle bad trials 
def Problem_Trials(bad_trial,clip_wav,AWflag_wav,FSFflag_wav):     
    """
    Warn user of problem trial recording names 
    
    Parameters
    ----------
    bad_trial : set
        names of trials flagged for potential problems
    clip_wav : set    
        names of trials flagged for clipping
    AWflag_wav : set
        names of trials flagged for their dBA values
    FSFflag_wav : set     
        names of trials flagged for their FSF scores   

    Returns
    -------

    """
    np.disp('The following trials were flagged as potentially having issues')
    np.disp(bad_trial)
    np.disp('The following trials were flagged for clipping')
    np.disp(clip_wav)
    np.disp('The following trials were flagged for their a-weight')
    np.disp(AW_flag)
    np.disp('The following trials were flagged for their FSF scores')
    np.disp(FSFflag_wav) 

           
def main():   
    """
    Read in a directory of WAV files. 
    Use a-weight, FSF, and clipping checks to inform
    user of potential problems in collected data. Flags
    trials that may require further investigation.

    Parameters
    ----------
    Wav_Dir : string
        directory of WAV files

    Returns
    -------

    """
    # Input parsing
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-wd",
        "--Wav_Dir",
        default=None,
        type=str,
        dest="Wav_Dir",
        help="Directory to test data wav files",
    )
    # Parse input arguments
    args = parser.parse_args()

if __name__ == "__main__":
    main()
  