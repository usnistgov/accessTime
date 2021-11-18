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

def Test_Stats(Wav_Dir,Rec = False,Progress = 500):
    '''
    Test_Stats Read in a directory of WAV files. 
    Use a-weight, FSF, and clipping checks to inform
    user of potential problems in collected data. Use 
    various measurements to detect trials that may
    have problems, such as clipping, dropped audio, 
    distortion
    '''

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
        rx_rec.append(y_rec[:,0])   
  
    # Create bad trial list
    bad_trial = []
   
    
   
#A-weight evaluation by rx recording
def AW_Rec_Check(Trials, rx_rec,fs,all_wavs, bad_trial):
    # Create empty list for a-weight     
    A_Weight = []
      
    # Get A-weight, plot recordings and periodogram if desired
    print("Gathering Statistics and Creating Plots") 
    for k in range(0,Trials): 
        # Calculate the A-Weighted power of each recording 
        aw = mcvqoe.base.a_weighted_power(rx_rec[k], fs) 
        A_Weight.append(aw)

    # A-Weight plot
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

    # Calculate average a-weight, standard deviation.
    # Use this info to find trials that may have lost
    # audio. 
    AW_lin = 10**(A_Weight/20)
    AW_Mean = round(statistics.mean(AW_lin),3)
    AW_std = round(statistics.stdev(AW_lin),3)
    for m in range(0,Trials):
        # Cycle through AW values, look for trials where the values
        # stand out by being a certain distance from the mean
        if abs(AW_lin[m]-AW_Mean) > AW_std:
            # Get the name of the wav file
            clip_wav = all_wavs[m]
            # Add it to the bad list
            bad_trial.append(clip_wav)


    # FSF
    # Calculate FSF scores, standard deviation.
    # Use this info to find trials that may have lost
    # audio.
    # Create empty list for a-weight     
    FSF_all = []
      
    # Get FSF scores, plot trials
    print("Gathering Statistics and Creating Plots") 
    for k in range(0,Trials): 
        get_fsf = mcvqoe.base.fsf(rx_rec[k], fs)
        FSF_all.append(get_fsf)


def Clip_Rec_Check(Trials, rx_rec, all_wavs,bad_trial):
    # Recordings and clip check
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
            bad_trial.append(clip_wav)
    
    
def Clip_Plot(rx_rec,Trials):   
    # Plot audio recording
    # Create empty list for time (seconds)
    tsec = []
    # Prepare time info for plotting
    for k in range(0,Trials):
        t = len(rx_rec[k])/fs
        ts = np.arange(0,t,1/fs)
        tsec.append(ts)
        # Plot recording
        dfTest= pd.DataFrame({"test":ts, 
                        "audio":rx_rec[:,0]})
    dfTest.set_index('test')
    fig = px.line(dfTest, y='audio',x='test')
    fig.update_layout(title_text='Trial Recordings')
    fig.update_xaxes(title_text='Time (s)')
    fig.update_yaxes(title_text='Amplitude')
    fig.show()    

# Handle bad trials 
def problem_trials(bad_trial):
    # Check if trial names repeat
    # Warn user of problem trial recording names


def main():   
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
    
    parser.add_argument(
        "-r",
        "--Rec",
        action="store_true",
        default=False,
        dest="Rec",
        help="Plot waveform recordings",
    )
    parser.add_argument(
        "-p",
        "--Progress",
        type=int, 
        nargs='+',
        default=500,
        dest="Progress",
        help="Display progress every n trials"
    )   
    # Parse input arguments
    args = parser.parse_args()

if __name__ == "__main__":
    main()
  