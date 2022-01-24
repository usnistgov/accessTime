import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
# TODO for my testing, not in final 
pio.renderers.default = 'browser'
import json


class Diagnostics_Eval():
    """
    Plot diagnostics and inform user of potential problems in collected
    data.
    
    Parameters
    ----------
    csv_dir : string
        path to diagnostics csv
    
    Attributes
    ----------   
    fs : int 
        sampling rate of rx recordings       
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
    clip_flag : list
        Trials that clipped  
    fsf_flag : list
        Trials that have low FSF scores or otherwise deviate 
        from the patterns of the dataset
    aw_flag : list
        Trials that have low dBA values (and likely lost audio)
        or otherwise deviate from the patterns of the dataset     
         
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
        aw_flag = diagnostics_dat.AW_flag
        self.aw_flag = aw_flag.to_numpy()
        clip_flag = diagnostics_dat.Clip_flag
        self.clip_flag = clip_flag.to_numpy()
        fsf_flag = diagnostics_dat.FSF_flag
        self.fsf_flag = fsf_flag.to_numpy() 
        
        # TODO add json part here
    
    def fsf_plot(self):
        """
        Plot the FSF of every trial.  
        
        Returns
        -------
        None.
    
        """
        # Plot FSF values   
        x_axis = list(range(1,self.trials+1))
        dfFSF = pd.DataFrame({"FSF Score": self.fsf_all,
                              "Trial": x_axis,
                              "fsf_flag": self.fsf_flag})
        # Separate out flagged trials for easy plotting
        df_flag = dfFSF[dfFSF['fsf_flag'] == 1]
        fig = go.Figure()
        # plot all trials
        fig.add_trace(
            go.Scatter(
            x = dfFSF['Trial'],    
            y = dfFSF['FSF Score'],
            mode = 'markers',
            showlegend = True,
            name = 'FSF score',
            marker = dict(
                size = 10,
                color = '#0000FF',
            symbol = dfFSF.fsf_flag
                )
            )
        ), 
        # Plot all flagged trials
        fig.add_trace(
            go.Scatter(
            x = df_flag['Trial'],    
            y = df_flag['FSF Score'],
            mode = 'markers',
            showlegend = True,
            name = 'FSF score - flagged',
            marker = dict(
                size = 10,
                color ='red',
                symbol = 'square'
                )
            )
        ),        
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
        x_axis = list(range(1,self.trials+1))
        dfAW = pd.DataFrame({"A-Weight": self.a_weight,
                             "Trial": x_axis,
                             "aw_flag":self.aw_flag})
        # Separate out flagged trials for easy plotting
        df_flag = dfAW[dfAW['aw_flag'] == 1]
        fig = go.Figure()
        # plot all trials
        fig.add_trace(
            go.Scatter(
                x = dfAW['Trial'], 
                y = dfAW['A-Weight'],
                mode = 'markers',
            showlegend = True,
            name = 'A-weight',
            marker = dict(
                size = 10,
                color = '#0000FF',
            symbol = dfAW.aw_flag
                )
            )
        ), 
        # Plot all flagged trials
        fig.add_trace(
            go.Scatter(
            x = df_flag['Trial'],    
            y = df_flag['A-Weight'],
            mode = 'markers',
            showlegend = True,
            name = 'A-weight - flagged',
            marker = dict(
                size = 10,
                color ='red',
                symbol = 'square'
                )
            )
        ),
        fig.update_layout(title_text='A-Weighted Power of Received Audio')
        fig.update_xaxes(title_text='Trial Number')
        fig.update_yaxes(title_text='A-Weight (dBA)')
        fig.show()
    
    def peak_dbfs_plot(self):
        """
        Plot the peak dbfs of every trial.    
        
        Returns
        -------
        None.
    
        """
        # Plot the peak amplitude (dbfs) for all trials   
        x_axis = list(range(1,self.trials+1))
        df_peak = pd.DataFrame({"Peak_dbfs": self.peak_dbfs,
                             "Trial": x_axis,
                             "clip_flag": self.clip_flag})  
        # Separate out flagged trials for easy plotting
        df_flag = df_peak[df_peak['clip_flag'] == 1]        
        fig = go.Figure()
        # Plot all trials
        fig.add_trace(
            go.Scatter(
                x = df_peak['Trial'], 
                y = df_peak['Peak_dbfs'],
                mode = 'markers',
                showlegend = True,
                name = 'Peak amplitude',
                marker = dict(
                size = 10,
                color = '#0000FF',
                symbol = df_peak.clip_flag
                )
            )
        ), 
        # Plot all flagged trials
        fig.add_trace(
            go.Scatter(
            x = df_flag['Trial'],    
            y = df_flag['Peak_dbfs'],
            mode = 'markers',
            showlegend = True,
            name = 'Peak amplitude - flagged',
            marker = dict(
                size = 10,
                color ='red',
                symbol = 'square'
                )
            )
        ),       
        fig.update_layout(title_text='Peak Amplitude of Received Audio')
        fig.update_xaxes(title_text='Trial Number')
        fig.update_yaxes(title_text='Peak Amplitude (dBfs)')
        fig.show()      