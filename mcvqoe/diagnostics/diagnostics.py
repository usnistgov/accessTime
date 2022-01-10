import os
import fnmatch
import mcvqoe.base
import argparse
import pandas as pd
import math
import re
import statistics

class Diagnose():
    """
   Diagnose Class to perform diagnostic evaluation of received
    audio files and confirm data integrity.
     
    Use a-weight, FSF, and clipping checks to inform
    user of potential problems in collected data. Flags
    trials that may require further investigation.
    
    Parameters
    ----------
    Wav_Dir : string
        directory of WAV files
    
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
                 Wav_Dir = ''):
        self.Wav_Dir = Wav_Dir
        # Read in a directory of test trial wav files.
        # Get all the Rx wav files 
        Dir_Files = os.listdir(self.Wav_Dir)
        Naming = 'Rx*'
        all_wavs = fnmatch.filter(Dir_Files, Naming)
        # Get total number of trials
        self.Trials = len(all_wavs)
        # Create empty list for rx recordings 
        self.rx_rec = []
        self.rx_dat = []
        # Cycle through, in order
        # TODO: be clear about testing file formats. This gets confused if
        # the RX numbers reset for each file like in access time
        for n in range(1,self.Trials+1):
            start = 'Rx'+str(n)+'_'
            rx_name = [s for s in all_wavs if start in s]
            rx_path = self.Wav_Dir + '/' + rx_name[0]
            # Check how many channels we have 
            self.fs,y_rec = mcvqoe.base.audio_read(rx_path)
            self.rx_rec.append(y_rec[:,0]) 
            self.rx_dat.append(rx_name[0])
            # Find all the Tx files in the wav_dir, strip 
            # the Tx and .wav off 
            TX_names = 'Tx*'
            TX_obj = fnmatch.filter(Dir_Files, TX_names)
            self.TX_filename =fnmatch.filter(TX_obj, '*.wav')
            # Create empty list for tx wavs 
            self.tx_wavs = []
            if TX_obj:
                # Cycle through and get all the TX files
                for k in range(0,len(self.TX_filename)):
                    tx_path = self.Wav_Dir + '/' + self.TX_filename[k]
                    self.fs,tx_wavfile = mcvqoe.base.audio_read(tx_path)
                    self.tx_wavs.append(tx_wavfile)
            # TODO be robust to scenarios where TX audio is not
            # saved to the data folder        
            # if there are no TX files in the dat dir, find them
    
    def aw_calc(self):
        """
        Calculates the a-weight (dBA) of each trial.
    
        Returns
        -------
        A_Weight : array
            A_Weight of every trial 
        """
        # Create empty list for a-weight values     
        A_Weight = []
          
        # Get A-weight
        for k in range(0,self.Trials): 
            # Calculate the A-weighted power of each recording 
            aw = mcvqoe.base.a_weighted_power(self.rx_rec[k], self.fs) 
            A_Weight.append(aw)
    
        return A_Weight
    
    def fsf_calc(self):   
        """
        Calculate FSF scores of each trial. 
    
        Returns
        -------
        FSF_all : list
           FSF scores of every trial 
        """
        # Create empty list for FSF scores
        FSF_all = []
        
        # Cycle through, match RX names to tx names
        # Get just the names of tx files, remove the Tx and .wav 
        tx_base = []
        for n in range(0,len(self.TX_filename)):
            tx_justname = re.sub('\.wav$', '', self.TX_filename[n])
            tx_justname = tx_justname[3:]
            tx_base.append(tx_justname)   
    
        for j in range(0,self.Trials): 
            # Find RX files with the matching tx name, create groups 
            match_wavs = re.match(r'(Rx\d+_(?P<tx_base_name>[^.]+))',self.rx_dat[j])
            # find the index of the TX and RX clips to match with the lists of 
            # wav data
            TX_idx = tx_base.index(match_wavs.group('tx_base_name'))
            TX_wav = self.tx_wavs[TX_idx]
            RX_wav = self.rx_rec[j]
            # Get FSF scores for each tx-rx pair
            get_fsf = mcvqoe.base.fsf(RX_wav,TX_wav,self.fs)
            # Get just the FSF score
            FSF_all.append(get_fsf[0])   
    
        return FSF_all

    def peak_amp_calc(self):
        """
        Cycle through all rx recordings and get peak amplitude.

        Returns
        ------- 
        peak_dbfs : list
            peak amplitude of each trial, dB relative to full 
            scale 
        """
        # Create empty list for peak volume
        peak_dbfs = []
        for n in range(0,self.Trials):
            # check for positive and negative clipping
            peak = max(abs(self.rx_rec[n]))
            peak_db = round(20 * math.log10(peak), 2)
            peak_dbfs.append(peak_db)
        return peak_dbfs
    #TODO rethink flagging to better fit CSV export (1 and 0)
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
        
    def gather_diagnostics(self,A_Weight,FSF_all,peak_dbfs,clip_flag,fsf_flag,aw_flag):
        """
        Create a dataframe of all diagnostic data. A-weight,
        FSF scores, max clip amplitude. Convert to json, csv
        
        Parameters
        ----------
        A_Weight : list    
            A-Weight across all RX trials 
        FSF_all : list
            FSF scores across all RX trials
        peak_dbfs : list     
            Peak amplitude across all RX trials   
        clip_flag : set
            Trials that clipped    
        fsf_flag : set
            Trials that have low FSF scores or otherwise deviate 
            from the patterns of the dataset
        aw_flag : set
            Trials that have low dBA values (and likely lost audio)
            or otherwise deviate from the patterns of the dataset         
        
        Returns
        -------
        diagnostics_csv : csv 
            CSV containing all the dat for diagnostics measurements
       """
       # Create dataframe of info
        df_Diagnostics = pd.DataFrame({"RX_Name":self.rx_dat, 
                        "A_Weight":A_Weight,
                        "FSF_Scores":FSF_all,
                        "Peak_Amplitude":peak_dbfs})
        # Get session name and use that to name files 
        test_path, test_name =re.split("wav/+", self.Wav_Dir)
        # Create json
        diagnostics_json = df_Diagnostics.to_json()
        with open(os.path.join(self.Wav_Dir,'diagnostics.json'),'w') as f:
            f.write(diagnostics_json) 
        # Create csv    
        diagnostics_csv = df_Diagnostics.to_csv(index=False, line_terminator='\n')
        with open(os.path.join(self.Wav_Dir,'diagnostics.csv'),'w') as f:
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
        "Wav_Dir",
        default=None,
        type=str,
        help="Directory to test data wav files",
    )
    # Parse input arguments
    args = parser.parse_args()
    obj = Diagnose(args.Wav_Dir)
    print("Measuring a-weight") 
    A_Weight = obj.aw_calc()
    print("Measuring FSF") 
    FSF_all = obj.fsf_calc()
    print("Measuring peak amplitude") 
    peak_dbfs = obj.peak_amp_calc()
    print("Creating json and csv") 
    obj.gather_diagnostics(A_Weight, FSF_all, peak_dbfs)

if __name__ == "__main__":
    main()
  