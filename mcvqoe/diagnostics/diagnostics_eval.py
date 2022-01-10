import statistics
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import plotly.express as px
# TODO for my testing, not in final 
pio.renderers.default = 'browser'


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