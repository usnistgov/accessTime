# -*- coding: utf-8 -*-
"""
Created on Tue Dec 21 08:31:44 2021

@author: cjg2
"""
import os
import fnmatch
import mcvqoe.base
import statistics
import argparse
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import plotly.io as pio
import plotly.express as px
import math
import re
import json

class diagnostics_eval():
    """
    Plot data and inform user of potential problems in collected
    data. Flags trials that may require further investigation.
    """

def load_csv(csv_dir):
    """
    Read in a diagnostics csv path.  

    Parameters
    ----------
    csv_dir : string
        Path to diagnostics csv

    Returns
    -------
    None.

    """
    
    # Read csv, convert to dataframe
    diagnostics_dat = pd.read_csv(csv_dir)

def Clip_Flag(Trials,peak_dbfs,rx_dat,bad_trial):
    """
    Cycle through the peak amplitude and check
    for clipping.

    Parameters
    ----------
    Trials : int
        number of trials
    rx_dat : list
        names of rx recordings 
    bad_trial : TYPE
        DESCRIPTION.
    peak_dbfs : list
        peak amplitude of each trial, dB relative to full 
        scale     

    Returns
    -------
    clip_flag : set
        Trials that clipped 
    bad_trial : set
        Names of all trials that set off any of the flags for 
        potential problems

    """
    # Set up warning threshold
    vol_high = -1
    # Create empty set for peak volume and flag
    clip_flag = set()
    
    # Check for positive and negative clipping
    for n in range(0,Trials):
        # If approaching clipping, flag as a bad trial
        if peak_dbfs[n] > vol_high :
            # Get the name of the wav file
            clip_wav = rx_dat[n]
            # Add it to the bad list
            bad_trial.add(clip_wav)
            clip_flag.add(clip_wav)
    return clip_flag, bad_trial    

def FSF_Plot(FSF_all,Trials):
    """
    Plot the FSF of every trial. 
    
    Parameters
    ----------
    FSF_all : list
        FSF scores of every trial
    Trials : int
        number of trials   
    
    Returns
    -------
    None.

    """
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
    
def FSF_Flag(FSF_all,Trials,rx_dat):
    """
    Check for trials with an FSF a certain distance
    from the mean. Use this info to find trials that 
    may have lost audio.
    
    Parameters
    ----------
    FSF_all : list
       FSF scores of every trial
    Trials : int
       number of trials   
    rx_dat : list
        names of rx recordings
        
    Returns
    -------
    FSF_flag : set
        Trials that have low FSF scores or otherwise deviate 
        from the patterns of the dataset
    bad_trial : set
        Names of all trials that set off any of the flags for 
        potential problems
    """
    # Create empty set for FSF flag    
    FSF_flag = set()
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
            
    return bad_trial, FSF_flag            
    
def AW_Plot(A_Weight,Trials):
    """
    Plot the a-weight of every trial. 
    
    Parameters
    ----------
    A_Weight : array
        A_Weight of every trial
    Trials : int
        number of trials   
    
    Returns
    -------
    None.

    """
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

def AW_Flag(A_Weight,Trials,rx_dat):
    """
    Check for trials with a dBA less than -60 dBA. Check 
    for trials with a dBA a certain distance from the 
    mean.
    
    Parameters
    ----------
    A_Weight : array
        A_Weight of every trial
    Trials : int
        number of trials
    rx_dat : list
        names of rx recordings    

    Returns
    -------
    bad_trial : set
        Names of all trials that set off any of the flags for 
        potential problems      
    AW_flag : set
        Trials that have low dBA values (and likely lost audio)
        or otherwise deviate from the patterns of the dataset 

    """
    # Create empty  set for a-weight flag     
    AW_flag = set()
    
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
           
        return AW_flag, bad_trial           

def Wav_Plot(rx_rec, Trials, fs):
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
    
 
def Problem_Trials(bad_trial, Clip_flag, AW_flag, FSF_flag):     
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