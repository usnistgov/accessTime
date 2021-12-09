# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 14:26:30 2021

@author: wrm3
"""
# =============================================================================
# Import statements
# =============================================================================
import argparse
import os
import re
import warnings

import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

import mcvqoe.math

def find_session_csvs(session_id, data_path):
    data_csvs = os.listdir(data_path)
    
    sesh_search = re.compile(f'{session_id}_.+.csv')
    
    return list(filter(sesh_search.match, data_csvs))
# =============================================================================
# Class definitions
# =============================================================================
class AccessData():
    """

        Parameters
        ----------
        test_names : TYPE
            DESCRIPTION.
        test_path : TYPE, optional
            DESCRIPTION. The default is ''.
        wav_dirs : TYPE, optional
            DESCRIPTION. The default is [].
        use_reprocess : TYPE, optional
            DESCRIPTION. The default is True.
         : TYPE
            DESCRIPTION.
            
        Attributes
        ----------
        data : pd.DataFrame
            DESCRIPTION
        test_names : list
            DESCRIPTION
        test_info : dict
            DESCRIPTION
        cps : dict
            DESCRIPTION

        Returns
        -------
        None.

    """
    def __init__(self,
                 test_names,
                 test_path='',
                 wav_dirs=[],
                 use_reprocess=True,
                 ):
       
        self.use_reprocess = use_reprocess
        
        if isinstance(test_names, str):
            test_names = [test_names]
        if isinstance(wav_dirs, str):
            wav_dirs = [wav_dirs]

        if not wav_dirs:
            wav_dirs = (None, ) * len(test_names)
        
        # Initialize info arrays
        self.test_names = []
        self.test_info = dict()
        
        # Loop through all the tests and find files
        for tn, wd in zip(test_names, wav_dirs):
            # split name to get path and name
            # if it's just a name all goes into name
            dat_path, name = os.path.split(tn)
            # Split extension, ext is empty if none
            t_name, ext = os.path.splitext(name)
            
            # Check if a path was given to a .csv file
            if not dat_path and not ext == '.csv':
                # Generate using test_path
                dat_path = os.path.join(test_path, 'csv')
                # Find all csvs that match session id t_name
                dat_file = find_session_csvs(session_id=t_name,
                                              data_path=dat_path,
                                              )
                cp_path = os.path.join(test_path, 'wav')
            else:
                
                if test_path == '':
                    # Assume full path given
                    dat_file = [tn]
                    cp_path = os.path.join(os.path.dirname(dat_path), 'wav')
                    dat_path = ''
                    
                else:
                    # Assume we are supposed to use test path too
                    dat_file = [os.path.join(test_path, 'csv', tn)]
                    cp_path = os.path.join(test_path, os.path.dirname(dat_path), 'wav')
                    
            
            # Check if we were given an explicit wav directory
            if wd:
                # Use given path
                cp_path = wd
                # get test name from wav path
                
            else:
                # Otherwise get path to the wav dir
                
                # Remove possible R in t_name
                wt_name = t_name.replace('Rcapture', 'capture')
                
                sesh_search_str = re.compile('(capture_.+_\d{2}-\w{3}-\d{4}_\d{2}-\d{2}-\d{2})')
                sesh_search = sesh_search_str.search(wt_name)
                sesh_id = sesh_search.groups()[0]
                cp_path = os.path.join(cp_path, sesh_id)
            
            self.test_info[t_name] = {'data_path': dat_path,
                                     'data_file': dat_file,
                                     'cp_path': cp_path}
            self.test_names.append(t_name)
            self.data, self.cps = self.load_sessions()
            
    def load_sessions(self):
        """
        Load access time sessions and associated cutpoints files

        Returns
        -------
        tests : TYPE
            DESCRIPTION.
        tests_cp : TYPE
            DESCRIPTION.

        """
        
        tests = pd.DataFrame()
        tests_cp = {}
        for session, sesh_info in self.test_info.items():
            for word_csv in sesh_info['data_file']:
                fname = os.path.join(sesh_info['data_path'], word_csv)
                if self.use_reprocess:
                    # Look for reprocessed file if it exists
                    fname = self.check_reprocess(fname)
                
                test = pd.read_csv(fname, skiprows=3)
                
                # Store test name as column in test
                sesh_search_str = re.compile('(capture_.+_\d{2}-\w{3}-\d{4}_\d{2}-\d{2}-\d{2})')
                sesh_search = sesh_search_str.search(session)
                sesh_id = sesh_search.groups()[0]
                test['name'] = sesh_id
                
                # Extract talker word combo from file name
                tw_search_str = r'([FM]\d)(_b\d{1,2}_w\d_)(\w+)(?:.csv)'
                tw_search_var = re.compile(tw_search_str)
                tw_search = tw_search_var.search(word_csv)
                if tw_search is None:
                    import pdb; pdb.set_trace()
                talker, bw_index, word = tw_search.groups()
                talker_word = talker + ' ' +  word
                # Store as column
                test['talker_word'] = talker_word
                
                
                # Load cutpoints, store in dict
                cp_name = 'Tx_' + talker + bw_index + word + '.csv'
                cp_path = os.path.join(sesh_info['cp_path'], cp_name)
                
                tests_cp[talker_word] = pd.read_csv(cp_path)
                
                
                with open(fname) as head_file:
                    audio_files = head_file.readline()
                    sample_rate = head_file.readline()
                
                fs_search_var = re.compile(r'\d+')
                fs_search = fs_search_var.search(sample_rate)
                if fs_search is not None:
                    fs = int(fs_search.group())
                else:
                    raise RuntimeError(f'No valid sample rate found in session header\n{fname}')
                
                # Determine length of T from cutpoints
                T = tests_cp[talker_word].loc[0]['End']/fs
                
                # Store PTT time relative to start of P1 
                test['time_to_P1'] = T - test['PTT_time']
                tests = tests.append(test)
        
        return tests, tests_cp
    
    def check_reprocess(self, fname):
        """
        Look for a reprocessed data file in same path as fname.

        Searches for a reprocessed data file in same path as fname.
        Reprocessed data always starts as 'Rcapture', where original data
        starts with 'capture'. Returns reprocessed file name if it exists,
        otherwise returns original file name.

        Parameters
        ----------
        fname : str
            Path to a session csv file.

        Returns
        -------
        str:
            Path to reprocessed file if it exits, otherwise returns fname

        """
        dat_path, name = os.path.split(fname)
        if 'Rcapture' not in name:
            reprocess_fname = os.path.join(dat_path, 'R{}'.format(name))
            if os.path.exists(reprocess_fname):
                out_name = reprocess_fname
            else:
                out_name = fname
        else:
            out_name = fname

        return out_name


    def _get_data(self, test_names, test_path, wav_dirs):
        
        try:
            dat = []
            header = []
            for session in test_names:
                sesh_name = os.path.join(test_path, session)
                # Grab main data, skipping extra header info
                dat.append(pd.read_csv(sesh_name, skiprows=3))
                # Grab extra header info
                header_dat = pd.read_csv(sesh_name,
                                         sep='=',
                                         nrows=2,
                                         header=None,
                                         usecols=[1]).transpose()
                header_dat.columns = ['Wav file', 'fs']
                header.append(header_dat)
            # dat = [pd.read_csv(test_path + session, skiprows=3) for session in test_names]
            # header_dat = [pd.read_csv(test_path + session, sep='=', nrows=2,
            #                           header=None, usecols=[1]) for session in test_names]
            # header_dat = [hd.transpose() for hd in header_dat]
            # for hd in header_dat:
            #     hd.columns=["Wav file", "fs"]
            return dat, header
        except(FileNotFoundError) as err:
            print(f"Session files can not be found. {err}")

    def _get_cut_points(self, cut_names, cut_dir):
        try:
            cut_points = [pd.read_csv(cut_dir + cut) for cut in cut_names]
            return(cut_points)
        except(FileNotFoundError) as err:
            print(f"Session files can not be found. {err}")

    def _get_sampling_frequency(self):
        if not all([(dat["fs"] == self.header_dat[0].iloc[0]["fs"]).any() for dat in self.header_dat]):
            raise ValueError("Different sampling frequencies.")
        else:
            return self.header_dat[0]["fs"]

    def _get_audio_clips(self):
        # cheap, easy etraction of the word from the header data
        audio_clips = [fname["Wav file"] for fname in self.header_dat]
        return(audio_clips)

    def _get_speaker_word(self):
        # cheap, easy etraction of the word from the header data
        speaker_words = [fname.iloc[0]["Wav file"][:-4].split("_")[-1] for fname in self.header_dat]
        return(speaker_words)

    # TODO: Reimplement this
    # def __repr__(self):
    #     s = f'''AccessData object:
    #         Speaker words: {self.speaker_word}
    #         Sampling frequency: {self.sampling_frequency.iloc[0]}'''
    #     return s

class FitData:

    def __init__(self, I0, t0, lam, covar, curve_dat):
        self.I0 = I0
        self.t0 = t0
        self.lam = lam
        self.covar = covar
        self.curve_dat = curve_dat

class evaluate:
    """
    Parameters
    ----------
    test_names : str or list
        Name of test, or list of names of tests.

    test_path : str
        Path where test data is stored. Does not need to be passed if
        test_names contains full paths to files and wav_dirs is set as
        well.

    wav_dirs : str or list
        Paths to directories containing audio for a PSuD test. Must contain
        cutpoints for audio clips in data files.

    test_type : str
        DESCRIPTION.
    ptt_session_names : TYPE, optional
        DESCRIPTION. The default is None.
    **kwargs : TYPE
        DESCRIPTION.

    Returns
    -------
    None.
    """

    def __init__(self,
                 test_names,
                 cut_names,
                 test_path,
                 wav_dirs=[],
                 # TODO: Come up with better default for test_type
                 test_type=None,
                 ptt_session_names=None,
                 json_data=None,
                 **kwargs):
        
        

        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise TypeError(f'{k} is not a valid keyword argument')
        
        # Data loaded in
        self.data = AccessData(test_names, cut_names, test_path, wav_dirs)
        # TODO: Come up with clean way to handle correction_data
        # self.correction_data = None if not ptt_session_names else AccessData(ptt_session_names, cut_names, session_dir, cut_dir)
        self.fit_type = self._get_fit_type(test_type)
        self.fit_data = None

        # Data from fit
        self.fit_data = None

    def _get_fit_type(self, fit_type):
        valid_fit_types = ["COR", "LEG"]
        if not fit_type in valid_fit_types:
            raise ValueError(f"Fit type not one of: {valid_fit_types}")
        return fit_type

    def __repr__(self):
        s = f'''evaluate object:
            Speaker words: {self.data.speaker_word}
            Sampling frequency: {self.data.sampling_frequency.iloc[0]}
            Test type: {self.fit_type}'''
        return s

    def fit_curve_data(self):
        # Fit SUT tests
        recenter = [cp["End"][0]/int(self.data.sampling_frequency) for cp in self.data.cut_points]
        fresh_dat = [dat[["PTT_time", "P1_Int"]] for dat in self.data.dat]
        for ii in range(len(recenter)):
            fresh_dat[ii]["PTT_time"] = recenter[ii] - fresh_dat[ii]["PTT_time"]

        # Legacy fit
        if self.fit_type == "LEG":
            # join dataframes
            curve_dat = pd.concat(fresh_dat)

            # Calculate asymptotic int
            I0 = np.mean([np.mean(x["P2_Int"]) for x in self.data.dat])

            # logistic function to fit
            def logistic_fit(xdata, t0, lam):
                return I0/(1+np.exp((xdata-t0)/lam))

            # TODO: Attempt predictive paramter fit

            # Naieve guess
            init = [0, -0.1]
            fit_dat = curve_fit(logistic_fit, curve_dat["PTT_time"], curve_dat["P1_Int"], p0=init)

            # store as fit data and return
            return FitData(I0, fit_dat[0][0], fit_dat[0][1], fit_dat[1], curve_dat)

        if self.test_type == "COR":
            # needs ptt tests to use correction factor
            if not self.ptt_session_names:
                raise ValueError("Correction factor requires PTT tests.")
            return 0


    def eval_intell(self):
        pass

    def eval_access(self):
        pass

    def eval(self):
        pass


# =============================================================================
# Ancillary functions
# =============================================================================
def pretty_print(evaluate):
    pass


# =============================================================================
# Main definition
# =============================================================================
def main():
    # # set up parser
    # parser = argparse.ArgumentParser(description=__doc__)

    # parser.add_argument('session_files', type=str, nargs='+', action='extend',
    #                     help='Test names')
    # parser.add_argument('cut_files', type=str, nargs='+', action='extend',
    #                     help='Cut files corresponding to session files.')
    # parser.add_argument('-sp', '--session-path', default='', type=str,
    #                     help='Path to directory containing the session files, defaults to current directory.')
    # parser.add_argument('-cp', '--cut-path', default='', type=str,
    #                     help='Path to directory containing the cut files, defaults to current directory.')
    # parser.add_argument('-tt', '--test-type', default='SUT', type=str,
    #                     help='Path to directory containing the cut files, defaults to current directory.')

    # # Get arguments for use in evaluate class
    # args = parser.parse_args()
    # t = evaluate(args.session_files, args.cut_files,
    #              args.session_path, args.cut_path,
    #              args.test_type)

    # res = t.eval()

    # # Pretty print result and return
    # pretty_print(res)
    # return(res)

    eta = evaluate(
        ['Rcapture_P25_Direct_Access_Time_18-Oct-2019_07-38-54_F1_b39_w4_hook.csv',
         'Rcapture_P25_Direct_Access_Time_22-Oct-2019_07-25-17_F3_b15_w5_west.csv',
         'Rcapture_P25_Direct_Access_Time_23-Oct-2019_14-11-36_M3_b22_w3_cop.csv',
         'Rcapture_P25_Direct_Access_Time_25-Oct-2019_13-22-20_M4_b18_w4_pay.csv'],
        ['Tx_F1_b39_w4_hook.csv', 'Tx_F3_b15_w5_west.csv',
         'Tx_M3_b22_w3_cop.csv', 'Tx_M4_b18_w4_pay.csv'],
        'C:/Users/wrm3/Desktop/Access Time Addendum Paper Data/P25-Direct-2500-ms/',
        'C:/Users/wrm3/Desktop/Access Time Addendum Paper Data/P25-Direct-2500-ms/',
        'LEG')

    u = eta.fit_curve_data()
    print(u)

# =============================================================================
# Execute if run as main script
# =============================================================================
if __name__ == "__main__":
    main()
