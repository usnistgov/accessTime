import os
import fnmatch
import mcvqoe.base
import statistics
import argparse
import numpy as np
import pandas as pd
import math
import re
import json

class diagnose():
    """
   diagnose Class to perform diagnostic evaluation of received
    audio files and confirm data integrity.
    
    Read in a directory of WAV files. 
    Use a-weight, FSF, and clipping checks to inform
    user of potential problems in collected data. Flags
    trials that may require further investigation.
    
    Parameters
    ----------
    Wav_Dir : string
        directory of WAV files
    
    Attributes
    ----------
    
    Methods
   ----------

    See Also
    --------

    Examples
    --------

    
    Returns
    -------
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
    """
def load_dat(Wav_Dir):    
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
   
        return TX_filename, tx_wavs, Trials, rx_rec, fs, rx_dat, bad_trial
    
def AW_Rec_Check(Trials, rx_rec, fs, rx_dat, bad_trial):
    """
    Calculates the a-weight (dBA) of each trial.
    
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
    A_Weight : array
        A_Weight of every trial 
    """
    # Create empty list for a-weight values     
    A_Weight = []
      
    # Get A-weight
    print("Gathering Statistics and Creating Plots") 
    for k in range(0,Trials): 
        # Calculate the A-weighted power of each recording 
        aw = mcvqoe.base.a_weighted_power(rx_rec[k], fs) 
        A_Weight.append(aw)

    return A_Weight

def FSF_Rec_Check(TX_filename,tx_wavs,Trials,rx_rec,fs,rx_dat,bad_trial):   
    """
    Calculate FSF scores of each trial. 
    
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

    Returns
    -------
    FSF_all : list
       FSF scores of every trial 
     
    """
    # Create empty list for FSF scores
    FSF_all = []
    
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
        # Get just the FSF score
        FSF_all.append(get_fsf[0])   

    return FSF_all

def Clip_Rec_Check(Trials,rx_rec,rx_dat,bad_trial):
    """
    Cycle through all rx recordings and get peak amplitude.
    
    Parameters
    ----------
    Trials : int
        number of trials 
    rx_rec : list 
        audio for rx recordings         
    rx_dat : list
        names of rx recordings   

    Returns
    ------- 
    peak_dbfs : list
        peak amplitude of each trial, dB relative to full 
        scale 
    """
    # Create empty list for peak volume
    peak_dbfs = []

    for n in range(0,Trials):
        # Find peak amplitude (abs)
        peak = max(abs(rx_rec[n]))
        peak_db = round(20 * math.log10(peak), 2)
        peak_dbfs.append(peak_db)
    
    return peak_dbfs       

def Gather_Diagnostics(rx_dat,A_Weight,FSF_all,peak_dbfs):
    """
    Create a dataframe of all diagnostic data. A-weight,
    FSF scores, max clip amplitude. Convert to json, csv
    
    Parameters
    ----------
    rx_dat : list
        Names of all RX trials
    A_Weight : list    
        A-Weight across all RX trials 
    FSF_all : list
        FSF scores across all RX trials
    peak_dbfs : list     
        Peak amplitude across all RX trials   

    Returns
    -------
    diagnostics_dat : json 
        Dataframe containing all the dat for diagnostics
   """
   # Create dataframe of info
    df_Diagnostics = pd.DataFrame({"RX_Name":rx_dat, 
                    "A_Weight":A_Weight,
                    "FSF_Scores":FSF_all,
                    "Amplitude":peak_dbfs})
    # TODO Set dir for testing    
    Test_Dir = 'C:/Users/cjg2/Documents/MCV'
    # Create json
    diagnostics_json = df_Diagnostics.to_json()
    with open(os.path.join(Test_Dir,'diagnostics_json.json'),'w') as f:
        f.write(diagnostics_json) 
    # Create csv    
    diagnostics_csv = df_Diagnostics.to_csv()
    with open(os.path.join(Test_Dir,'diagnostics_json.json'),'w') as f:
        f.write(diagnostics_csv)
        
    return diagnostics_json, diagnostics_csv    

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
  