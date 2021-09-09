# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 14:26:30 2021

@author: wrm3
"""
# =============================================================================
# Import statements
# =============================================================================
import argparse
import warnings

import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

import mcvqoe.math


# =============================================================================
# Class definitions
# =============================================================================
class AccessData(object):
    def __init__(self, session_names, cut_names, session_dir, cut_dir):
        self.dat, self.header_dat = self._get_data(session_names, session_dir)
        self.cut_points = self._get_cut_points(cut_names, cut_dir)
        self.sampling_frequency = self._get_sampling_frequency()
        self.audio_clips = self._get_audio_clips()
        self.speaker_word = self._get_speaker_word()
        
    def _get_data(self, session_names, session_dir):
        try:
            dat = [pd.read_csv(session_dir + session, skiprows=3) for session in session_names]
            header_dat = [pd.read_csv(session_dir + session, sep='=', nrows=2,
                                      header=None, usecols=[1]) for session in session_names]
            header_dat = [hd.transpose() for hd in header_dat]
            for hd in header_dat:
                hd.columns=["Wav file", "fs"]
            return (dat, header_dat)
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

class evaluate(object):
    def __init__(self, session_names, cut_names, session_dir, cut_dir, test_type):
        # Data loaded in
        self.access_data = AccessData(session_names, cut_names, session_dir, cut_dir)
        self.fit_type = self._get_fit_type(test_type)
        self.fit_data = None
        
        # Data from fit
        self.fit_data = None
    
    def _get_fit_type(self, fit_type):
        valid_fit_types = ["PTT", "SUT", "COR", "LEG"]
        if not fit_type in valid_fit_types:
            raise ValueError(f"Fit type not one of: {valid_fit_types}")
        return fit_type
    
    def fit_data(self):
        pass
    
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

    eta = AccessData(
        ['capture_PTT-gate-2500ms_24-Nov-2020_07-24-31_F3_b31_w2_law.csv'],
        ['F3_b31_w2_law.csv'],
        'C:/Users/wrm3/Desktop/accesstime_local_data/csv/',
        'C:/Users/wrm3/Desktop/accesstime_local_data/wav/T_2500ms-varyFilled/')

# =============================================================================
# Execute if run as main script
# =============================================================================
if __name__ == "__main__":
    main()
