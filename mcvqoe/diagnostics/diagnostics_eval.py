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
import plotly.express as px


class diagnostics_eval():
    """
    Plot diagnostics and inform user of potential problems in collected
    data. Flags trials that may require further investigation.
    
    Parameters
    ----------
    csv_dir : string
        path to diagnostics csv
    
    Attributes
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
    
    Methods
   ----------

    See Also
    --------

    Examples
    --------
    
    Returns
    -------
    
    """
    def __init__(self, 
                 csv_dir = ''):
        self.csv_dir = csv_dir
    
    # TODO add this to init 
        """
        Read in a diagnostics csv path.  
    
        Returns
        -------
         rx_name : list
             names of rx recordings 
         A_Weight : array
             A_Weight of every trial    
        FSF_all : list
             FSF scores of every trial
         peak_dbfs : list
             peak amplitude of each trial, dB relative to full 
             scale      
         Trials : int
             number of trials
        """
        
        # Read csv, convert to dataframe
        diagnostics_dat = pd.read_csv(self.csv_dir)
        # TODO: make these naming conventions from the csvs
        # make functional sense 
        rx_name = diagnostics_dat.RX_Name
        self.rx_name = rx_name.to_numpy()
        A_Weight = diagnostics_dat.A_Weight
        self.A_Weight = A_Weight.to_numpy()
        FSF_all = diagnostics_dat.FSF_Scores
        self.FSF_all = FSF_all.to_numpy()
        peak_dbfs = diagnostics_dat.Amplitude
        self.peak_dbfs = peak_dbfs.to_numpy()
        self.trials = len(diagnostics_dat)
        
    
    def Clip_Flag(self):
        """
        Cycle through the peak amplitude and check
        for clipping.  
    
        Returns
        -------
        clip_flag : set
            Trials that clipped 
    
        """
        # Set up warning threshold
        vol_high = -1
        # Create empty set for peak volume and flag
        clip_flag = set()
        
        # Check for positive and negative clipping
        for n in range(0,self.rials):
            # If approaching clipping, flag as a bad trial
            if self.peak_dbfs[n] > vol_high :
                # Get the name of the wav file
                clip_wav = self.rx_name[n]
                # Add it to the bad list
                clip_flag.add(clip_wav)
        return clip_flag   
    
    def FSF_Plot(self):
        """
        Plot the FSF of every trial.  
        
        Returns
        -------
        None.
    
        """
        # Plot FSF values 
        FSF_Scores = np.asarray(self.FSF_all)  
        x_axis = list(range(1,self.trials+1))
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
        
    def FSF_Flag(self):
        """
        Check for trials with an FSF a certain distance
        from the mean. Use this info to find trials that 
        may have lost audio.
            
        Returns
        -------
        FSF_flag : set
            Trials that have low FSF scores or otherwise deviate 
            from the patterns of the dataset
        """
        # Create empty set for FSF flag    
        FSF_flag = set()
        # Gather metrics for FSF scores
        FSF_Mean = round(statistics.mean(self.FSF_all),3)
        FSF_std = round(statistics.stdev(self.FSF_all),3)
        for m in range(0,self.trials):
            # Cycle through FSF scores, look for trials where the score
            # stands out by being a certain distance from the mean
            if abs(self.FSF_all[m]-FSF_Mean) > 2*FSF_std:
                # Get the name of the wav file
                FSFflag_wav = self.rx_name[m]
                # Add it to the bad list
                FSF_flag.add(FSFflag_wav)
            # Add a flag for low FSF scores that may be a sign of 
            # dropped audio
            if self.FSF_all[m] < 0.3:
                # Add it to the bad list
                FSF_flag.add(FSFflag_wav)
                
        return FSF_flag            
        
    def AW_Plot(self):
        """
        Plot the a-weight of every trial.    
        
        Returns
        -------
        None.
    
        """
        # Plot a-weighted power for all trials  
        A_Weight = np.asarray(self.A_Weight)  
        x_axis = list(range(1,self.trials+1))
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
    
    def AW_Flag(self):
        """
        Check for trials with a dBA less than -60 dBA. Check 
        for trials with a dBA a certain distance from the 
        mean.   
    
        Returns
        -------     
        AW_flag : set
            Trials that have low dBA values (and likely lost audio)
            or otherwise deviate from the patterns of the dataset 
    
        """
        # Create empty  set for a-weight flag     
        AW_flag = set()
        
        # Calculate mean a-weight, standard deviation.
        # Use this info to find trials that may have lost
        # audio. 
        AW_lin = 10**(self.A_Weight/20)
        AW_low = 10**(-60/20)
        AW_Mean = round(statistics.mean(AW_lin),3)
        AW_std = round(statistics.stdev(AW_lin),3)
        for m in range(0,self.trials):
            # Cycle through AW values, look for trials where the values
            # stand out by being a certain distance from the mean
            if abs(AW_lin[m]-AW_Mean) > 2*AW_std:
                # Get the name of the wav file
                AWflag_wav = self.rx_name[m]
                # Add it to the bad list
                AW_flag.add(AWflag_wav)
            # Add a flag if the a-weight is below -60 dBA
            if AW_lin[m] < AW_low:
               # Get the name of the wav file
               AWflag_wav = self.rx_name[m]
               # Add it to the bad list
               AW_flag.add(AWflag_wav)
               
        return AW_flag           
    
    def Wav_Plot(self,fs):
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
        for k in range(0,self.trials):
            t = len(self.rx_rec[0])/fs
            ts = np.arange(0,t,1/fs)
            tsec.append(ts)
            # Plot recording
            dfWavs= pd.DataFrame({"time":ts, 
                            "audio":self.rx_rec[0]})
        dfWavs.set_index('time')
        fig = px.line(dfWavs, y='audio',x='time')
        fig.update_layout(title_text='Trial Recordings')
        fig.update_xaxes(title_text='Time (s)')
        fig.update_yaxes(title_text='Amplitude')
        fig.show()  
        
     
    def Problem_Trials(Clip_flag, AW_flag, FSF_flag):     
        """
        Warn user of problem trial recording names 
        
        Parameters
        ----------
        Clip_flag : set    
            names of trials flagged for clipping
        AW_flag : set
            names of trials flagged for their dBA values
        FSF_flag : set     
            names of trials flagged for their FSF scores   
    
        Returns
        -------
    
        """
        if Clip_flag:
            np.disp('The following trials were flagged for clipping')
            np.disp(Clip_flag)  
        if AW_flag:    
            np.disp('The following trials were flagged for their a-weight')
            np.disp(AW_flag)
        if FSF_flag:    
            np.disp('The following trials were flagged for their FSF scores')
            np.disp(FSF_flag) 