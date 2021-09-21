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

    def __repr__(self):
        s = f'''AccessData object:
            Speaker words: {self.speaker_word}
            Sampling frequency: {self.sampling_frequency.iloc[0]}'''
        return s

class FitData(object):

    def __init__(self, I0, t0, lam, covar, curve_dat):
        self.I0 = I0
        self.t0 = t0
        self.lam = lam
        self.covar = covar
        self.curve_dat = curve_dat

class evaluate(object):

    def __init__(self, session_names, cut_names, session_dir, cut_dir, test_type, ptt_session_names=None):
        # Data loaded in
        self.sut_access_data = AccessData(session_names, cut_names, session_dir, cut_dir)
        self.ptt_access_data = None if not ptt_session_names else AccessData(ptt_session_names, cut_names, session_dir, cut_dir)
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
            Speaker words: {self.sut_access_data.speaker_word}
            Sampling frequency: {self.sut_access_data.sampling_frequency.iloc[0]}
            Test type: {self.fit_type}'''
        return s

    def fit_curve_data(self):
        # Fit SUT tests
        recenter = [cp["End"][0]/int(self.sut_access_data.sampling_frequency) for cp in self.sut_access_data.cut_points]
        fresh_dat = [dat[["PTT_time", "P1_Int"]] for dat in self.sut_access_data.dat]
        for ii in range(len(recenter)):
            fresh_dat[ii]["PTT_time"] = recenter[ii] - fresh_dat[ii]["PTT_time"]

        # Legacy fit
        if self.fit_type == "LEG":
            # join dataframes
            curve_dat = pd.concat(fresh_dat)

            # Calculate asymptotic int
            I0 = np.mean([np.mean(x["P2_Int"]) for x in self.sut_access_data.dat])

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
