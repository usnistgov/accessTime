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
from scipy import curve_fit

import mcvqoe.math

# =============================================================================
# Class definitions
# =============================================================================
class evaluate(object):
    def __init__(self, session_names, cut_names, session_dir, cut_dir):
        # ToDo: validation logic here as well.
        try:
            self.dat = [pd.read_csv(session_dir + session, skiprows=3) for session in session_names]
        except:
            pass

        try:
            self.cut_points = [pd.read_csv(cut_dir + cut, skiprows=3) for cut in cut_names]
        except:
            pass
        self.sampling_frequency = None
        self.audio_clips = None
        self.speaker_word = None

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
    # set up parser
    parser = argparse.ArgumentParser(descrption=__doc__)

    parser.add_argument('session_files', type=str, nargs='+', action='extend',
                        help='Test names')
    parser.add_argument('cut_files', type=str, nargs='+', action='extend',
                        help='Cut files corresponding to session files.')
    parser.add_argument('-sp', '--session-path', default='', type=str,
                        help='Path to directory containing the session files, defaults to current directory.')
    parser.add_argument('-cp', '--cut-path', default='', type=str,
                        help='Path to directory containing the cut files, defaults to current directory.')

    # Get arguments for use in evaluate class
    args = parser.parse_args()
    t = evaluate(args.session_files, args.cut_files,
                 session_dir=args.sessoin_path, cut_dir=args.cut_path)

    res = t.eval()

    # Pretty print result and return
    pretty_print(res)
    return(res)

# =============================================================================
# Execute if run as main script
# =============================================================================
if __name__ == "__main__":
    main()
