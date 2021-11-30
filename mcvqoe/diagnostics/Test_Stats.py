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
    bad_trial : set
        Names of all trials that set off any of the flags for 
        potential problems

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
    rx_dat = []
    # Cycle through, in order
    for n in range(1,Trials+1):
        start = 'Rx'+str(n)+'_'
        rx_name = [s for s in all_wavs if start in s]
        rx_path = Wav_Dir + '/' + rx_name[0]
        fs,y_rec = mcvqoe.base.audio_read(rx_path)
        rx_rec.append(y_rec[:]) 
        rx_dat.append(rx_name[0])
    # Create bad trial set
    bad_trial = set()
    # Find all the Tx files in the wav_dir, strip 
    # the Tx and .wav off 
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
   
def AW_Rec_Check(Trials, rx_rec,fs,rx_dat,bad_trial):
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
    rx_dat : list
        names of rx recordings   
    bad_trial : set
        Names of all trials that set off any of the flags for 
        potential problems

    Returns
    -------
    bad_trial : set
        Names of all trials that set off any of the flags for 
        potential problems      
    AW_flag : set
        Trials that have low dBA values (and likely lost audio)
        or otherwise deviate from the patterns of the dataset 
    """
    # Create empty list, set for a-weight values and flag     
    A_Weight = []
    AW_flag = set()
      
    # Get A-weight
    print("Gathering Statistics and Creating Plots") 
    for k in range(0,Trials): 
        # Calculate the A-weighted power of each recording 
        aw = mcvqoe.base.a_weighted_power(rx_rec[k], fs) 
        A_Weight.append(aw)

    # Plot a-weighted power for all trials  
    A_Weight = np.asarray(A_Weight)  
    x_axis = list(range(1,Trials+1))
    dfAW = pd.DataFrame({"A-Weight": A_Weight,
                         "Trials": x_axis})  
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x = dfAW['Trials'], 
            y = dfAW['A-Weight'],
            mode = 'markers'
        )
    )    
    fig.update_layout(title_text='A-Weighted Power of Received Audio')
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
        if abs(AW_lin[m]-AW_Mean) > 2*AW_std:
            # Get the name of the wav file
            AWflag_wav = rx_dat[m]
            # Add it to the bad list
            bad_trial.add(AWflag_wav)
            AW_flag.add(AWflag_wav)
        # Add a flag if the a-weight is below -60 dBA
        if AW_lin[m] < AW_low:
           # Get the name of the wav file
           AWflag_wav = rx_dat[m]
           # Add it to the bad list
           AW_flag.add(AWflag_wav)

def FSF_Rec_Check(TX_filename,tx_wavs,Trials, rx_rec,fs,rx_dat,bad_trial):   
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
    rx_dat : list
        names of rx recordings   
    bad_trial : set
        Names of all trials that set off any of the flags for 
        potential problems

    Returns
    -------
    FSF_flag : set
        Trials that have low FSF scores or otherwise deviate 
        from the patterns of the dataset 
    bad_trial : set
        Names of all trials that set off any of the flags for 
        potential problems
    """
    # Create empty list,set for FSF scores and flag    
    FSF_all = []
    FSF_flag = set()
    
    # Get FSF scores, plot trials
    print("Gathering FSF data") 
    # Cycle through, match RX names to tx names
    # Get just the names of tx files, remove the Tx and .wav 
    tx_base = []
    for n in range(0,len(TX_filename)):
        tx_justname = re.sub('\.wav$', '', TX_filename[n])
        tx_justname = tx_justname[3:]
        tx_base.append(tx_justname)   

    for j in range(0,Trials): 
        # Find RX files with the matching tx name, create groups 
        match_wavs = re.match(r'(Rx\d+_(?P<tx_base_name>[^.]+))',rx_dat[j])
        # find the index of the TX and RX clips to match with the lists of 
        # wav data
        TX_idx = tx_base.index(match_wavs.group('tx_base_name'))
        TX_wav = tx_wavs[TX_idx]
        RX_wav = rx_rec[j]
        # Get FSF scores for each tx-rx pair
        get_fsf = mcvqoe.base.fsf(RX_wav,TX_wav,fs)
        FSF_all.append(get_fsf)   
        
    # Gather metrics for FSF scores
    FSF_Mean = round(statistics.mean(FSF_all),3)
    FSF_std = round(statistics.stdev(FSF_all),3)
    for m in range(0,Trials):
        # Cycle through FSF scores, look for trials where the score
        # stands out by being a certain distance from the mean
        if abs(FSF_all[m]-FSF_Mean) > 2*FSF_std:
            # Get the name of the wav file
            FSFflag_wav = rx_dat[m]
            # Add it to the bad list
            bad_trial.add(FSFflag_wav)
            FSF_flag.add(FSFflag_wav)
        # Add a flag for low FSF scores that may be a sign of 
        # dropped audio
        if FSF_all[m] < 0.3:
            # Add it to the bad list
            bad_trial.add(FSFflag_wav)
            FSF_flag.add(FSFflag_wav)
            
    # Plot FSF values 
    FSF_Scores = np.asarray(FSF_all)  
    x_axis = list(range(1,Trials+1))
    dfFSF = pd.DataFrame({"FSF Score": FSF_Scores,
                          "Trial": x_axis})  
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
        x = dfFSF['Trial'],    
        y = dfFSF['FSF Score'],
        mode = 'markers'
        )
    ) 
    fig.update_layout(title_text='FSF Score of Received Audio')
    fig.update_xaxes(title_text='Trial Number')
    fig.update_yaxes(title_text='FSF Score')
    fig.show()

def Clip_Rec_Check(Trials, rx_rec, rx_dat,bad_trial):
    """
    Cycle through all rx recordings and check if any clipped.
    Parameters
    ----------
    Trials : int
        number of trials 
    rx_rec : list 
        audio for rx recordings         
    rx_dat : list
        names of rx recordings   
    bad_trial : set
        Names of all trials that set off any of the flags for 
        potential problems

    Returns
    -------
    Clip_flag : set
        Trials that clipped 
    bad_trial : set
        Names of all trials that set off any of the flags for 
        potential problems
    """
    # Set up warning threshold
    vol_high = -1
    # Create empty list, set for peak volume and flag    
    peak_dbfs = []
    Clip_flag = set()
    for n in range(0,Trials):
        # check for positive and negative clipping
        peak = max(abs(rx_rec[n]))
        peak_db = round(20 * math.log10(peak), 2)
        peak_dbfs.append(peak_db)
        # If approaching clipping, flag as a bad trial
        if peak_dbfs[n] > vol_high :
            # Get the name of the wav file
            clip_wav = rx_dat[n]
            # Add it to the bad list
            bad_trial.add(clip_wav)
            Clip_flag.add(clip_wav)
    
    
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
        dfWavs= pd.DataFrame({"time":ts, 
                        "audio":rx_rec[0]})
    dfWavs.set_index('time')
    fig = px.line(dfWavs, y='audio',x='time')
    fig.update_layout(title_text='Trial Recordings')
    fig.update_xaxes(title_text='Time (s)')
    fig.update_yaxes(title_text='Amplitude')
    fig.show()    
 
def Problem_Trials(bad_trial,Clip_flag,AW_flag,FSF_flag):     
    """
    Warn user of problem trial recording names 
    
    Parameters
    ----------
    bad_trial : set
        Names of all trials that set off any of the flags for 
        potential problems
    Clip_flag : set    
        names of trials flagged for clipping
    AW_flag : set
        names of trials flagged for their dBA values
    FSF_flag : set     
        names of trials flagged for their FSF scores   

    Returns
    -------

    """
    np.disp('The following trials were flagged as potentially having issues')
    np.disp(bad_trial)
    if Clip_flag:
        np.disp('The following trials were flagged for clipping')
        np.disp(Clip_flag)  
    if AW_flag:    
        np.disp('The following trials were flagged for their a-weight')
        np.disp(AW_flag)
    if FSF_flag:    
        np.disp('The following trials were flagged for their FSF scores')
        np.disp(FSF_flag) 

           
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
  