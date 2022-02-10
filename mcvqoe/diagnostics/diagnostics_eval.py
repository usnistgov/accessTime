import json
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go

class evaluate():
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
                 wav_dir = None,
                 # csv_dir = '',
                 # test_name=None,
                 json_data=None):
        if json_data is None:
            # Ensure there is only one test passed
            if isinstance(wav_dir, list):
                if len(wav_dir) > 1:
                    raise ValueError(f'Can only process one TVO measurement at a time, {len(wav_dir)} passed.')
                else:
                    wav_dir = wav_dir[0]
            diag_name = 'diagnostics.csv'
            fname = os.path.basename(wav_dir)
            if fname == diag_name:
                # I got the full path to the diagnostics csv 
                fpath = wav_dir
            else:
                fpath = os.path.join(wav_dir, diag_name)
            
            self.test_name = fpath
            
            # Grab the data
            self.data = pd.read_csv(fpath)
            
        else:
            self.data, self.test_name = evaluate.load_json_data(json_data)

        
    def to_json(self, filename=None):
        """
        Create json representation of diagnostics data

        Parameters
        ----------
        filename : str, optional
            If given save to json file. Otherwise returns json string. The default is None.

        Returns
        -------
        final_json: json
            json version of diagnotsic data and flag conditions

        """
        test_info = dict([(self.test_name, '')])
        
        out_json = {
            'measurement': self.data.to_json(),
            'test_info': test_info,
            }
            
        # Final json representation of all data
        final_json = json.dumps(out_json)
        if filename is not None:
            with open(filename, 'w') as f:
                json.dump(out_json, f)
                
        return final_json  
    
    @staticmethod
    def load_json_data(json_data):
        """
        Do all data loading from input json_data

        Parameters
        ----------
        json_data : TYPE
            DESCRIPTION.

        Returns
        -------
        test_names : list
            DESCRIPTION.
        test_paths : dict
            DESCRIPTION.
        data : pd.DataFrame
            DESCRIPTION.

        """  
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
        # Extract data, cps, and test_info from json_data
        data = pd.read_json(json_data['measurement'])
        test_name = set(json_data['test_info'].keys())
        
        
        # Return normal Access data attributes from these
        return data, test_name
 

            
    def fsf_plot(self):
        """
        Plot the FSF of every trial.  
        
        Returns
        -------
        None.
    
        """
        # Plot FSF values   
        # x_axis = list(range(1,self.trials+1))
        # dfFSF = pd.DataFrame({"FSF Score": self.fsf_all,
        #                       "Trial": x_axis,
        #                       "fsf_flag": self.fsf_flag})
        # # Separate out flagged trials for easy plotting
        # df_flag = dfFSF[dfFSF['fsf_flag'] == 1]
        nrow, _ = self.data.shape
        
        df_flag = self.data[self.data['FSF_flag'] == 1]
        flag_indices = np.array([f'Trial: {i}' for i in df_flag.index+1])
        # df_flag.index + 1
        
        fig = go.Figure()
        # plot all trials
        fig.add_trace(
            go.Scatter(
            x = self.data.index,    
            y = self.data['FSF_Scores'],
            hovertext=np.array([f'Trial: {i}' for i in np.arange(1, nrow+1)]),
            mode = 'markers',
            showlegend = True,
            name = 'FSF score',
            marker = dict(
                size = 10,
                color = '#0000FF',
            symbol = self.data['FSF_flag']
                )
            )
        ), 
        # Plot all flagged trials
        fig.add_trace(
            go.Scatter(
            x = df_flag.index,    
            y = df_flag['FSF_Scores'],
            hovertext=flag_indices,
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
        fig.update_xaxes(title_text='Index')
        fig.update_yaxes(title_text='FSF Score')
        return fig      
        
    def aw_plot(self):
        """
        Plot the a-weight of every trial.    
        
        Returns
        -------
        None.
    
        """
        # # Plot a-weighted power for all trials    
        # x_axis = list(range(1,self.trials+1))
        # dfAW = pd.DataFrame({"A-Weight": self.a_weight,
        #                      "Trial": x_axis,
        #                      "AW_flag":self.aw_flag})
        # Separate out flagged trials for easy plotting
        nrow, _ = self.data.shape
        df_flag = self.data[self.data['AW_flag'] == 1]
        flag_indices = np.array([f'Trial: {i}' for i in df_flag.index+1])
        fig = go.Figure()
        # plot all trials
        fig.add_trace(
            go.Scatter(
                x = self.data.index, 
                y = self.data['A_Weight'],
                hovertext=np.array([f'Trial: {i}' for i in np.arange(1, nrow+1)]),
                mode = 'markers',
            showlegend = True,
            name = 'A-weight',
            marker = dict(
                size = 10,
                color = '#0000FF',
            symbol = self.data['AW_flag']
                )
            )
        ), 
        # Plot all flagged trials
        fig.add_trace(
            go.Scatter(
            x = df_flag.index,    
            y = df_flag['A_Weight'],
            hovertext=flag_indices,
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
        fig.update_xaxes(title_text='Index')
        fig.update_yaxes(title_text='A-Weight (dBA)')
        return fig
    
    def peak_dbfs_plot(self):
        """
        Plot the peak dbfs of every trial.    
        
        Returns
        -------
        None.
    
        """
        # Plot the peak amplitude (dbfs) for all trials   
        # x_axis = list(range(1,self.trials+1))
        # df_peak = pd.DataFrame({"Peak_Amplitude": self.peak_dbfs,
        #                      "Trial": x_axis,
        #                      "Clip_flag": self.Clip_flag})  
        # Separate out flagged trials for easy plotting
        nrow, _ = self.data.shape
        
        df_flag = self.data[self.data['Clip_flag'] == 1]        
        flag_indices = np.array([f'Trial: {i}' for i in df_flag.index+1])
        
        fig = go.Figure()
        # Plot all trials
        fig.add_trace(
            go.Scatter(
                x = self.data.index, 
                y = self.data['Peak_Amplitude'],
                hovertext=np.array([f'Trial: {i}' for i in np.arange(1, nrow+1)]),
                mode = 'markers',
                showlegend = True,
                name = 'Peak amplitude',
                marker = dict(
                size = 10,
                color = '#0000FF',
                symbol = self.data['Clip_flag']
                )
            )
        ), 
        # Plot all flagged trials
        fig.add_trace(
            go.Scatter(
            x = df_flag.index,    
            y = df_flag['Peak_Amplitude'],
            hovertext=flag_indices,
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
        fig.update_xaxes(title_text='Index')
        fig.update_yaxes(title_text='Peak Amplitude (dBfs)')
        return fig      