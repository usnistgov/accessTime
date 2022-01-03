# -*- coding: utf-8 -*-
"""
Created on Tue Dec 21 08:31:44 2021

@author: cjg2
"""
import statistics
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
pio.renderers.default = 'browser'
import pandas as pd
import plotly.express as px

class Diagnostics_Eval():
    """
    Plot diagnostics and inform user of potential problems in collected
    data. Flags trials that may require further investigation.
    
    Parameters
    ----------
    csv_dir : string
        path to diagnostics csv
    
    Attributes
    ----------   
    fs : int 
        sampling rate of rx recordings       
    rx_dat : list
        names of rx recordings
    rx_name : list
         names of rx recordings 
    a_weight : array
         A_Weight of every trial    
    fsf_all : list
         FSF scores of every trial
    peak_dbfs : list
         peak amplitude of each trial, dB relative to full 
         scale      
    trials : int
         number of trials
         
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
        # Read in a diagnostics csv path.  
        # Read csv, convert to dataframe
        diagnostics_dat = pd.read_csv(self.csv_dir)
        rx_name = diagnostics_dat.RX_Name
        self.rx_name = rx_name.to_numpy()
        a_weight = diagnostics_dat.A_Weight
        self.a_weight = a_weight.to_numpy()
        fsf_all = diagnostics_dat.FSF_Scores
        self.fsf_all = fsf_all.to_numpy()
        peak_dbfs = diagnostics_dat.Peak_Amplitude
        self.peak_dbfs = peak_dbfs.to_numpy()
        self.trials = len(diagnostics_dat)      
    
    def clip_flag(self):
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
        for n in range(0,self.trials):
            # If approaching clipping, flag as a bad trial
            if self.peak_dbfs[n] > vol_high :
                # Get the name of the wav file
                clip_wav = self.rx_name[n]
                # Add it to the bad list
                clip_flag.add(clip_wav)
        return clip_flag   
    
    def fsf_plot(self):
        """
        Plot the FSF of every trial.  
        
        Returns
        -------
        None.
    
        """
        # Plot FSF values 
        fsf_scores = np.asarray(self.fsf_all)  
        x_axis = list(range(1,self.trials+1))
        dfFSF = pd.DataFrame({"FSF Score": fsf_scores,
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
        
    def fsf_flag(self):
        """
        Check for trials with an FSF a certain distance
        from the mean. Use this info to find trials that 
        may have lost audio.
            
        Returns
        -------
        fsf_flag : set
            Trials that have low FSF scores or otherwise deviate 
            from the patterns of the dataset
        """
        # Create empty set for FSF flag    
        fsf_flag = set()
        # Gather metrics for FSF scores
        fsf_mean = round(statistics.mean(self.fsf_all),3)
        fsf_std = round(statistics.stdev(self.fsf_all),3)
        for m in range(0,self.trials):
            # Cycle through FSF scores, look for trials where the score
            # stands out by being a certain distance from the mean
            if abs(self.FSF_all[m]-fsf_mean) > 2*fsf_std:
                # Get the name of the wav file
                fsf_flag_wav = self.rx_name[m]
                # Add it to the bad list
                fsf_flag.add(fsf_flag_wav)
            # Add a flag for low FSF scores that may be a sign of 
            # dropped audio
            if self.fsf_all[m] < 0.3:
                # Add it to the bad list
                fsf_flag.add(fsf_flag_wav)
                
        return fsf_flag            
        
    def aw_plot(self):
        """
        Plot the a-weight of every trial.    
        
        Returns
        -------
        None.
    
        """
        # Plot a-weighted power for all trials  
        a_weight = np.asarray(self.a_weight)  
        x_axis = list(range(1,self.trials+1))
        dfAW = pd.DataFrame({"A-Weight": a_weight,
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
    
    def aw_flag(self):
        """
        Check for trials with a dBA less than -60 dBA. Check 
        for trials with a dBA a certain distance from the 
        mean.   
    
        Returns
        -------     
        aw_flag : set
            Trials that have low dBA values (and likely lost audio)
            or otherwise deviate from the patterns of the dataset 
    
        """
        # Create empty  set for a-weight flag     
        aw_flag = set()
        
        # Calculate mean a-weight, standard deviation.
        # Use this info to find trials that may have lost
        # audio. 
        aw_lin = 10**(self.a_weight/20)
        aw_low = 10**(-60/20)
        aw_mean = round(statistics.mean(aw_lin),3)
        aw_std = round(statistics.stdev(aw_lin),3)
        for m in range(0,self.trials):
            # Cycle through AW values, look for trials where the values
            # stand out by being a certain distance from the mean
            if abs(aw_lin[m]-aw_mean) > 2*aw_std:
                # Get the name of the wav file
                aw_flag_wav = self.rx_name[m]
                # Add it to the bad list
                aw_flag.add(aw_flag_wav)
            # Add a flag if the a-weight is below -60 dBA
            if aw_lin[m] < aw_low:
               # Get the name of the wav file
               aw_flag_wav = self.rx_name[m]
               # Add it to the bad list
               aw_flag.add(aw_flag_wav)
               
        return aw_flag           
    # TODO fix this for actual use case
    def wav_plot(self,fs):
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
     
    def problem_trials(clip_flag,aw_flag,fsf_flag):     
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
        if clip_flag:
            np.disp('The following trials were flagged for clipping')
            np.disp(clip_flag)  
        if aw_flag:    
            np.disp('The following trials were flagged for their a-weight')
            np.disp(aw_flag)
        if fsf_flag:    
            np.disp('The following trials were flagged for their FSF scores')
            np.disp(fsf_flag) 